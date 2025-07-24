#pylint:disable=import-error,line-too-long
"""This file is part of SME intellect Odoo Apps.
Copyright (C) 2023 SME intellect (<https://www.smeintellect.com>)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
"""
from odoo import api, modules, SUPERUSER_ID
import odoo

def post_load_hook():
    """ Get the database name from config"""
    db_name = odoo.tools.config.get('db_name')
    if not db_name:
        return
    registry = modules.registry.Registry.new(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Check if model is loaded
        if 'rabbitmq.consumer.controller' in env.registry.models:
            controllers = env['rabbitmq.consumer.controller'].sudo().search([('state', '=', 'running')])
            for controller in controllers:
                controller.action_start_consumer()
        else:
            # Model not loaded yet, skip
            pass

def uninstall_hook(env):
    """Stop all running consumers """
    controllers = env['rabbitmq.consumer.controller'].sudo().search([('state', '=', 'running')])
    for controller in controllers:
        controller.action_stop_consumer()
