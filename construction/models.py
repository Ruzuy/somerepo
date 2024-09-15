from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_defects_with_ratings(self):
        """Returns a list of defects with their associated expert ratings"""
        defects_with_ratings = []
        for defect in self.defects.all():
            ratings = defect.ratings.all()
            defects_with_ratings.append({
                'defect': defect,
                'ratings': ratings,
            })
        return defects_with_ratings


class Defect(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, related_name='defects', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Expert(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, related_name='experts', on_delete=models.CASCADE)
    defect = models.ForeignKey(Defect, related_name='ratings', on_delete=models.CASCADE)
    rating = models.IntegerField()

    def __str__(self):
        return self.name