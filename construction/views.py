from django.shortcuts import redirect, render, get_object_or_404
from construction.models import Project, Defect, Expert
from django.db.models import Avg


def index(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project, created = Project.objects.get_or_create(name=project_name)
        return redirect('formalization', pk=project.pk)

    # Получаем все проекты для отображения в меню
    projects = Project.objects.all()

    # Передаем список проектов в шаблон
    return render(request, 'index.html', {'projects': projects})


def formalization(request, pk):
    project = Project.objects.get(pk=pk)
    defects = project.defects.all()

    # Получаем уникальных экспертов
    experts = project.experts.values('name').distinct()

    experts_data = []
    for expert_data in experts:
        expert_name = expert_data['name']
        expert_ratings = []
        expert = Expert.objects.filter(name=expert_name, project=project).first()  # Получаем объект эксперта
        for defect in defects:
            # Фильтруем экспертов по имени
            rating = Expert.objects.filter(project=project, name=expert_name, defect=defect).first()
            if rating:
                expert_ratings.append(rating.rating)
            else:
                expert_ratings.append(None)  # Если нет рейтинга для этого дефекта

        # Рассчитываем среднее значение для рейтингов
        valid_ratings = [r for r in expert_ratings if r is not None]
        average_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 0

        # Добавляем данные эксперта
        experts_data.append({
            'expert_name': expert_name,
            'expert_id': expert.id,  # Добавляем ID эксперта для использования в шаблоне
            'ratings': expert_ratings,
            'average': round(average_rating, 2)  # Округляем до 2 знаков после запятой
        })

    if request.method == 'POST':
        if 'update_project_name' in request.POST:
            project.name = request.POST.get('project_name')
            project.save()
        elif 'add_defect' in request.POST:
            defect_name = request.POST.get('defect_name')
            Defect.objects.create(name=defect_name, project=project)
        elif 'add_expert' in request.POST:
            expert_name = request.POST.get('expert_name')
            for defect in defects:
                rating = request.POST.get(f'rating_{defect.id}')
                Expert.objects.create(name=expert_name, project=project, defect=defect, rating=rating)
        return redirect('formalization', pk=pk)

    return render(request, 'formalization.html', {
        'project': project,
        'defects': defects,
        'experts_data': experts_data,
    })


def save_project(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        # Здесь можно добавить логику для сохранения связанных дефектов и экспертов, если необходимо.
        # Например, сохранять какие-то изменения в связанных объектах.
        return redirect('index')  # Перенаправляем на главную страницу после сохранения


def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.delete()
    return redirect('index')


def delete_defect(request, defect_id):
    defect = get_object_or_404(Defect, id=defect_id)
    defect.delete()
    return redirect('formalization', pk=defect.project.id)


def delete_expert(request, expert_id):
    expert = get_object_or_404(Expert, id=expert_id)
    expert.delete()
    return redirect('formalization', pk=expert.project.id)