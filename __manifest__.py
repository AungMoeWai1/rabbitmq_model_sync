"""This file is part of SME intellect Odoo Apps.
Copyright (C) 2023 SME intellect (<https://www.smeintellect.com>).
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
"""
{
    'name':'RabbitMQ',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Real-time attendance syncing via RabbitMQ',
    'description': 'Real-time attendance syncing via RabbitMQ',
    'author': 'SME intellect',
    'website': "https://www.smeintellect.com",
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        #Sequence
        "data/ir_sequence.xml",

        #Cron service remove mechanism after two day
        "data/ir_cron_data.xml",

        #view
        "views/rabbitmq_consumer_control_view.xml",
        "views/rabbitmq_log_view.xml",

        #security
        "security/ir.model.access.csv"

    ],
    'external_dependencies': {
        'python': ['pika', 'pydantic', 'python-dotenv']
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'uninstall_hook': 'uninstall_hook',
    'post_load': 'post_load_hook',
}
