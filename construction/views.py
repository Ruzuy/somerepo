from math import fabs
from django.shortcuts import redirect, render, get_object_or_404
from .models import Project, Defect, Expert, Rating
from django.db.models import Avg



def index(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project, created = Project.objects.get_or_create(name=project_name)
        return redirect('show', pk=project.pk)

    # Get all projects for displaying in the menu
    projects = Project.objects.all()
    return render(request, 'index.html', {'projects': projects})

def show(request, pk):
    #breakpoint()
    project = Project.objects.get(pk=pk)
    defects = project.defects.all().order_by("created_at")
    experts = project.experts.all().order_by("created_at")
    rating_dict = {
        (rating.defect_id, rating.expert_id): rating
        for rating in Rating.objects.filter(defect__in=defects, expert__in=experts)
    }
    #breakpoint()
    experts_data = []
    deltas_data = []
    defect_averages = {}
    average_delta = 0
    third_table = {}

    # Рассчитываем средние оценки для каждого дефекта
    for defect in defects:
        average = Rating.objects.filter(defect=defect).aggregate(avg_mark=Avg('mark'))['avg_mark']
        defect_averages[defect.id] = average if average else 0

    # Собираем данные по каждому эксперту
    for expert in experts:
        expert_ratings = []
        expert_ratings_dict = {}
        for defect in defects:
            # Получаем рейтинг эксперта для конкретного дефекта
            rating = Rating.objects.filter(expert=expert, defect=defect).first()
            if rating:
                expert_ratings.append(rating.mark)
                expert_ratings_dict[defect.id] = rating.mark
            else:
                expert_ratings.append(None)  # Если нет рейтинга для этого дефекта

        # Рассчитываем среднюю оценку эксперта
        expert_average = sum(rating for rating in expert_ratings if rating) / len(defects) if defects else 0

        # Рассчитываем дельты (разницу между оценкой эксперта и средней оценкой по дефекту)
        deltas = [fabs(expert_ratings_dict.get(defect.id, 0) - defect_averages[defect.id]) for defect in defects]

        average_delta = 0
        if deltas:
            average_delta = sum(deltas) / len(deltas)

        experts_data.append({
            'expert_name': expert.name,
            'expert_id': expert.id,
            'ratings': expert_ratings,
            'average': expert_average,
            'average_delta': round(average_delta, 2),  # Добавляем среднюю дельту в данные эксперта
        })

        deltas_data.append({'expert_name': expert.name, 'deltas': deltas})

        # Вычисляем компетенцию для экспертов
        experts_data.sort(key=lambda x: x['average_delta'])
        for index, expert in enumerate(experts_data):
            expert['competence'] = index + 1


        # Вычисляем данные для третьей таблицы (формула)
        min_rating = min(r for r in expert_ratings) if any(expert_ratings) else 0
        max_rating = max(r for r in expert_ratings) if any(expert_ratings) else 0

        if max_rating != min_rating:  # чтобы избежать деления на ноль
            third_table[expert["expert_name"]] = [
                round(1 + ((rating - min_rating) * (len(defects) - 1)) / (max_rating - min_rating), 2) if rating else None
                for rating in expert_ratings
            ]
        else:
            third_table[expert["expert_name"]] = [1 for _ in expert_ratings]


    # Новая часть: расчеты для сумм, весов, отклонений и квадратов отклонений
    sums = [0] * len(defects)  # Для хранения суммы по каждому дефекту
    for expert_ratings in third_table.values():
        for i, rating in enumerate(expert_ratings):
            if rating is not None:
                sums[i] += rating


    # Среднее значение SUMA
    total_sum = sum(sums)
    average_sum = total_sum / len(defects) if defects else 0  # Используем количество дефектов для деления

    # Вычисляем отклонения и квадраты отклонений
    deviations = []
    squared_deviations = []

    for sum_value in sums:
        # Отклонение от среднего значения
        deviation = sum_value - average_sum
        squared_deviation = deviation ** 2  # Квадрат отклонения

        deviations.append(round(deviation, 2))
        squared_deviations.append(round(squared_deviation, 2))
    # Вычисляем вес

    weights = [round(s / total_sum, 2) if total_sum > 0 else 0 for s in sums]
    if request.method == 'POST':
        if 'update_project_name' in request.POST:
            project.name = request.POST.get('project_name')
            project.save()
        elif 'add_defect' in request.POST:
            defect_name = request.POST.get('defect_name')
            Defect.objects.create(name=defect_name, project=project)
        elif 'add_expert' in request.POST:
            expert_name = request.POST.get('expert_name')
            expert = Expert.objects.create(name=expert_name, project=project)
            for defect in defects:
                rating = request.POST.get(f'rating_{defect.id}')
                if rating:
                    Rating.objects.create(expert=expert, defect=defect, mark=float(rating))
        return redirect('show', pk=pk)


    return render(request, 'show.html', {
        'project': project,
        'defects': defects,
        'experts_data': experts_data,  # Добавили сюда данные со средней дельтой
        'defect_averages': [round(defect_averages[defect.id], 2) for defect in defects],
        'deltas_data': deltas_data,
        'average_delta': round(average_delta, 2),  # Добавляем среднюю дельту
        'third_table': third_table,
        'sums': sums,
        'total_sums': total_sum,
        'weights': weights,
        'average_sum': average_sum,
        'deviations': deviations,
        'squared_deviations': squared_deviations,
    })

def save_project(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        project.save()
        return redirect('index')


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    return redirect('index')

def delete_defect(request, defect_id):
    defect = get_object_or_404(Defect, id=defect_id)
    defect.delete()
    return redirect('show', pk=defect.project.id)

def delete_expert(request, expert_id):
    expert = get_object_or_404(Expert, id=expert_id)
    expert.delete()
    return redirect('show', pk=expert.project.id)