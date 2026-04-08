from django.shortcuts import render

# Create your views here.




def check_storage_quota(user,new_file_bytes:int)->tuple[bool,str]:#❓❓❓why -> used?

    is_paid=getattr(user,'is_paid',False)
    if is_paid:
        return True,""
    






















