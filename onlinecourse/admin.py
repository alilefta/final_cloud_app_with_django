from django.contrib import admin
# <HINT> Import any new Models here
from .models import Course, Lesson, Instructor, Learner, Question, Choice

# <HINT> Register QuestionInline and ChoiceInline classes here


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 5


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 5


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ['question_text', 'grade', 'get_choices_display']
    list_filter = ['question_text']
    search_fields = ['question_text']

    def get_choices_display(self, obj):
        choices = obj.choice_set.all()
        choice_texts = ", ".join([choice.choice_text for choice in choices])
        return choice_texts

    get_choices_display.short_description = 'Choices'


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'is_correct', 'question_text']
    list_filter = ['choice_text']
    search_fields = ['choice_text']

    def question_text(self, obj):
        return obj.question.question_text
# <HINT> Register Question and Choice models here


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
