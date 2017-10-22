import LocalSettings

def global_settings(request):
    # return any necessary values
    return {
        'PROJECT_NAME': LocalSettings.project_name,
    }