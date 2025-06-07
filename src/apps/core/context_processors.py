from .models import UserDocument

def user_profile_photo(request):
    if request.user.is_authenticated:
        profile_photo = UserDocument.objects.filter(user=request.user, document_name='profile_photo').first()
        if profile_photo:
            return {'profile_photo': profile_photo.file_path.url}
    return {}