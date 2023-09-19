from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(
            user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
    # Get user and course object, then get the associated enrollment object created when the user enrolled the course
    # Create a submission object referring to the enrollment
    # Collect the selected choices from exam form
    # Add each selected choice object to the submission object
    # Redirect to show_exam_result with the submission id
def submit(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        user = request.user
        enrollment = Enrollment.objects.get(
            course=course, user=user)
        print(enrollment)

        submission = Submission.objects.create(enrollment=enrollment)

        selected_choice_ids = extract_answers(request)

        for choice_id in selected_choice_ids:
            choice = get_object_or_404(Choice, pk=choice_id)
            submission.choices.add(choice)

        return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id, submission.id)))
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course_id, submission.id)))
# <HINT> A example method to collect the selected choices from the exam form from the request object


def extract_answers(request):
    submitted_anwsers = []
    for key, value in request.POST.items():
        if key.startswith('choice') or value == 'on':
            value = request.POST[key]
            choice_id = int(key.split('_')[1])
            submitted_anwsers.append(choice_id)
    return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
    # Get course and submission based on their ids
    # Get the selected choice ids from the submission record
    # For each selected choice, check if it is a correct answer or not
    # Calculate the total score

def calculate_question_grades(course, submission):
    questions = Question.objects.filter(course=course)

    question_grades = {}

    for question in questions:
        total_correct_choices = question.choice_set.filter(
            is_correct=True).count()

        selected_choices = submission.choices.filter(question=question)

        selected_correct_choices = selected_choices.filter(
            is_correct=True).count()

        selected_incorrect_choices = selected_choices.filter(
            is_correct=False).count()
        
        if total_correct_choices == 0:
            question_grade = 0.0
        else:

            penalty_per_incorrect_choice = 10
            correct_choices_score = (
                selected_correct_choices / total_correct_choices) * 100
            penalty_score = (selected_incorrect_choices *
                             penalty_per_incorrect_choice)
            
            question_grade = max(correct_choices_score - penalty_score, 0.0)

        question_grades[question.id] = question_grade

    return question_grades


def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    question_grades = calculate_question_grades(course, submission)

    choices_by_question = []

    for question in course.question_set.all():
        id_counter = 1
        choices_correctness = []
        for choice in question.choice_set.all():
            is_selected = choice.id in submission.choices.values_list('id', flat=True)
            choice_info = {
                'id': id_counter,
                'text': choice.choice_text,
                'correct': choice.is_correct,
                'selected': is_selected,
            }
            choices_correctness.append(choice_info)
            id_counter+=1
        choices_by_question.append({
            'question_text': question.question_text,
            'choices': choices_correctness,
            'question_id': question.id,
            'grade': question_grades.get(question.id, 0.0)
        })

    context['course'] = course
    context['submission'] = submission
    context['question_grades'] = question_grades
    context['grade'] = sum(question_grades.values()) / len(question_grades.keys())
    context['questions_no'] = len(question_grades.keys())
    context['choices_by_question'] = choices_by_question
    return render(request=request, template_name='onlinecourse/exam_result_bootstrap.html', context=context)
