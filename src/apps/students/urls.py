from django.urls import path
from .views import (StudentRegistrationView,
                    FeeStructureCreateView,
                    FeeStructureListView,
                    FeeStructureUpdateView,
                    AddFeeTypeView,
                    StudentAdmissionListView,
                    StudentUpdateView,
                    StudentDocumentUploadView,
                    PayFamilyFeeDuesView,
                    FamilyFeeDuesView,
                    admission_print_view,
                    promotion_class_selection,
                    bulk_promote_view,
                    DownloadStudentsListView,
                    BoardAcademicCreateView,
                    BoardAcademicUpdateView,
                    BoardAcademicListView,
                    StudentAdmissionUpdateView,
                    SelectSessionExamClassView,
                    SubjectListView,
                    MarksEntryView,
                    exam_course_subject_setup,
                    select_exam_course_view
                )

urlpatterns = [
    # Student URLs
    path('students/register/', StudentRegistrationView.as_view(), name='register_student'),
    path('students/', StudentAdmissionListView.as_view(), name='student_admission_list'),
    path('students/update/<uuid:pk>/', StudentUpdateView.as_view(), name='student_update'),
    path('students/document/upload/<uuid:pk>/', StudentDocumentUploadView.as_view(), name='student_document_upload'),
    # Fee Structure URLs
    path('fee/structure/create/', FeeStructureCreateView.as_view(), name='fee_structure_create'),
    path('fee/structure/', FeeStructureListView.as_view(), name='fee_structure_list'),
    path('fee/structure/update/<uuid:pk>/', FeeStructureUpdateView.as_view(), name='fee_structure_update'),
    path('fee/structure/<uuid:fee_structure_id>/add_fee_type/', AddFeeTypeView.as_view(), name='add_fee_type'),
    # Pay Family Fee Dues URLs
    path('pay/family/fee/dues/<uuid:family_id>/', PayFamilyFeeDuesView.as_view(), name='pay_family_fee_dues'),
    path('family/fee/dues/<uuid:family_id>/', FamilyFeeDuesView.as_view(), name='family_fee_dues'),
    # Admission Print URLs
    path('admission/print/<uuid:studentadmission_id>/', admission_print_view, name='admission_print'),
    path('students/promote/', promotion_class_selection, name='promotion_class_selection'),
    path('students/promote/<str:class_code>', bulk_promote_view, name='bulk_promote'),

    path('students/download/', DownloadStudentsListView.as_view(), name='download_students'),

    path('board-academic/create/', BoardAcademicCreateView.as_view(), name='board_create'),
    path('board-academic/<uuid:pk>/update/', BoardAcademicUpdateView.as_view(), name='board_update'),
    path('board-academic/', BoardAcademicListView.as_view(), name='board_list'),
    path('update-admission/<uuid:id>/', StudentAdmissionUpdateView.as_view(), name='update_admission'),
    
    path("select/", SelectSessionExamClassView.as_view(), name="select_exam_class"),
    path("subjects/<uuid:session_id>/<uuid:exam_id>/<uuid:course_id>/", 
         SubjectListView.as_view(), name="subject_list"),
    path("marks/<uuid:examcoursesubject_id>/<uuid:course_id>/", 
         MarksEntryView.as_view(), name="marks_entry"),
    path("exam-course-subjects/<uuid:exam_id>/<uuid:course_id>/", exam_course_subject_setup, name="exam_course_subjects"),
    path("select-exam-course/", select_exam_course_view, name="select_exam_course"),

]