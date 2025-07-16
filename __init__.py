# __init__.py
from .utils import rabbitmq_consumer
from . import models
# from odoo import api, SUPERUSER_ID
# import odoo

#To run the consumer when module is start installed
# def post_init_hook(env):
#     # env = api.Environment(cr, SUPERUSER_ID, {})
#     rabbitmq_consumer.start_rabbitmq_consumer()
#
# #To stop the consumer when module is uninstall/delete
# def uninstall_hook(env):
#     rabbitmq_consumer.stop_rabbitmq_consumer()
#
# #To re-run the consumer after odoo service is stop/restarted.
# def ready():
#     if odoo.evented:
#         return  # avoid duplicate consumer in workers
#     rabbitmq_consumer.start_rabbitmq_consumer()
# ready()
