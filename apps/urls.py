from django.urls import path
from . import views
import render
from django.urls import path

urlpatterns = [
    #===============User urls=====================
    
    path('login/', views.login_view, name='login'), 
    path('logout/', views.logout_view, name='logout'),# Main login handler
    #=============== Logout url ===================
    
   
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('image_view/', views.image_view, name='image_view'),
    path('gallery/', views.image_view, name='gallery_page'),
    path('student_details/', views.student_details, name='student_details'),
    
    #=============== Staff UI url ===========================
    path('staff/', views.staff, name='staff'),
    #============ Notes uploaded  url =====================
    path("upload_notes_staff/", views.upload_notes_staff, name="upload_notes_staff"),
    path('edit-note/<int:id>/update/', views.edit_note, name='edit_note'),
    path("delete-note/<int:id>/", views.delete_note, name="delete_note"),
    
    #=============== Staff Dashboard url =====================
    
    path("export_staff/", views.export_staff, name="export_staff"),
    # path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    #=============== Syllabus uploaded url ====================
    path('upload_syllabus/', views.upload_syllabus, name='upload_syllabus'),
    path("edit_syllabus/<int:id>/", views.edit_syllabus, name="edit_syllabus"),
    path("delete_syllabus/<int:id>/", views.delete_syllabus, name="delete_syllabus"),
    path('settings/', views.site_settings, name='settings'),

    #===============Admin url===================================
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('enquiry/', views.Messages_details, name='enquiry'),
    path('enquiry-list/', views.Enquiry_View, name='enquiry_list'),
    path('add-course/', views.course_details, name='add_course'),
    path('course-details/', views.course_details, name='course_details'),
    path('admission_details/', views.admission_management, name='admission_details'),
    path('certification_details/', views.certification_management, name='certification_details'),
    #==================Gallery_update=========================
    path('gallery_upload/', views.gallery_upload, name='gallery_upload'),
    path('gallery_view/', views.gallery_view, name='gallery_view'),
    path('enquiry-success/', lambda request: render(request, 'success.html'), name='enquiry_success'),
    
    
    #===================== Students url===========================
    
    path("students/", views.student_details, name="student_details"),
    path('student_Enroll/', views.student_enroll, name='student_Enroll'),
    path("create/", views.student_create, name="student_create"),
    path('student/edit/<int:id>/', views.student_edit, name='student_edit'),
    path('student/delete/<int:id>/', views.student_delete, name='student_delete'),
    path("export/", views.export_students, name="export_students"),
    path("student_Enroll/<int:id>/", views.view_stu, name="view_stu"),
    path('check-email/', views.check_email, name='check_email'),
    

    # path('dashboard/<str:stu_id>/', views.student_dashboard, name='student_dashboard'),
    
    #=================== Certificate url =========================
    path('certification_details/', views.certification_management, name='certification_management'),
    path('upload-certificate/', views.upload_certificate, name='upload_certificate'),
    path('verify/<str:cert_id>/', views.verify_certificate, name='verify_certificate'),
    path('download/<str:cert_id>/', views.download_certificate, name='download_certificate'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('certification_details/', views.certification_management, name='certification_management'),
    path('bulk-update-certificates/', views.bulk_update_certificates, name='bulk_update_certificates'),
    
    # =========Dashboards==========
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("export_staff/", views.export_staff, name="export_staff"),
    path('staff_register/', views.staff_register, name='staff_register')
]  

    
    

