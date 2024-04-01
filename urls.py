from web_tools.tools import include

urlpatterns = [
    include('First_app.urls').url_list,
    include('Log_user.urls').url_list,
]