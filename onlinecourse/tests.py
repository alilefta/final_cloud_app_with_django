from django.test import TestCase
from .models import Course, Question, Choice, Submission, Enrollment
from django.urls import reverse
from django.contrib.auth.models import User
import json

# Create your tests here.
class CourseModelTestCase(TestCase):
    def test_course_creation(self):
        course = Course.objects.create(
            name="Test Course",
            description="This is a test course."
        )
        self.assertEqual(course.name, "Test Course")
        self.assertEqual(course.description, "This is a test course.")

class CourseListViewTestCase(TestCase):
    def test_course_list_view(self):
        Course.objects.create(name="Course 1", description="Description 1")
        Course.objects.create(name="Course 2", description="Description 2")
        
        response = self.client.get(reverse('onlinecourse:index'))
        
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(
            response.context['course_list'],
            ['<Course: Name: Course 1,Description: Description 1>', '<Course: Name: Course 2,Description: Description 2>'],
            ordered=False
        )


class CourseDetailViewTestCase(TestCase):
    def test_course_detail_view(self):
        course = Course.objects.create(name="Course 1", description="Description 1")
        response = self.client.get(reverse('onlinecourse:course_details', args=(course.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['course'], course)


class CourseEnrollmentTestCase(TestCase):
    def test_course_enrollment(self):
        course = Course.objects.create(name="Course 1", description="Description 1")
        response = self.client.get(reverse('onlinecourse:enroll', args=(course.id,)))
        self.assertEqual(response.status_code, 302)


# class CourseSubmitTestCase(TestCase):
#     def test_course_submit(self):
#         course = Course.objects.create(name="Course 1", description="Description 1")
#         response = self.client.get(reverse('onlinecourse:exam_submission', args=(course.id, )))
#         self.assertEqual(response.status_code, 302)

class ExamSubmissionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )

        self.course = Course.objects.create(
            name="Test Course",
            description="This is a test course."
        )

        self.question1 = Question.objects.create(
            course=self.course,
            question_text="Question 1",
            grade=10.0
        )
        self.choice1_1 = Choice.objects.create(
            question=self.question1,
            choice_text="Choice 1",
            is_correct=True
        )
        self.choice2_1 = Choice.objects.create(
            question=self.question1,
            choice_text="Choice 2",
            is_correct=False
        )
        self.enrollment = Enrollment.objects.create(
            user=self.user,
            course=self.course,
            mode=Enrollment.AUDIT 
        )

    def test_exam_submission(self):
        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(reverse('onlinecourse:exam_submission', args=[self.course.id,]), {
            f'choice_{self.choice1_1.id}': 'on'
        })
        
        self.assertEqual(response.status_code, 302)


        submission = Submission.objects.filter(enrollment=self.enrollment).first()
        self.assertIsNotNone(submission)

        selected_choices = submission.choices.all()
        
        self.assertEqual(selected_choices.count(), 1)
        self.assertEqual(selected_choices.first(), self.choice1_1)

        expected_grade = self.question1.grade * 10.0

        response = self.client.get(reverse('onlinecourse:show_exam_result', args=[self.course.id, self.enrollment.id]), {'grade': expected_grade})
        grade = response.context['grade']
        
        self.assertEqual(grade, expected_grade)
        self.assertEqual(response.status_code, 200)
        




class TemplateTestCase(TestCase):
    def test_index_template(self):
        response = self.client.get(reverse('onlinecourse:index'))
        self.assertTemplateUsed(response, 'onlinecourse/course_list_bootstrap.html')

    def test_detail_template(self):
        course = Course.objects.create(name="Course 1", description="Description 1")
        response = self.client.get(reverse('onlinecourse:course_details', args=(course.id,)))
        self.assertTemplateUsed(response, 'onlinecourse/course_detail_bootstrap.html')

    def test_login_template(self):
        response = self.client.get(reverse('onlinecourse:login'))
        self.assertTemplateUsed(response, 'onlinecourse/user_login_bootstrap.html')


