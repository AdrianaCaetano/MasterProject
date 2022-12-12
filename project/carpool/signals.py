
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
# #from django.contrib.auth.models import Candidates          # sender
# from .models import Carpools, Candidates                    # receiver

# @receiver(post_save, sender=Candidates)
# def post_save_create_carpools(sender, instance, created,dispatch_uid='create_new_carpool', **kwargs):
#     print('sender', sender)
#     print('instance', instance)
#     print('created', created)
#     if created:
#         print('Create new carpools')
#         # do something


# @receiver(post_delete, sender=Candidates)
# def post_delete_candidates(sender, **kwargs):
#     # when candidates are deleted, delete all carpools connected to these candidates
#     # Carpools.objects.all().delete()
#     print("Candidates and Carpools were deleted")


