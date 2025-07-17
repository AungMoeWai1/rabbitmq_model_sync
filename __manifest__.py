{
    'name':'RabbitMQ',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Real-time attendance syncing via RabbitMQ',
    'description': 'Real-time attendance syncing via RabbitMQ',
    'author': 'SME intellect',
    'website': "https://www.smeintellect.com",
    'depends': ['base', 'hr', 'hr_attendance', ],
    'data': [
        #Sequence
        "data/ir_sequence.xml",

        #Cron service remove mechanism after two day
        "data/ir_cron_data.xml",

        #view
        "views/rabbitmq_consumer_control_view.xml",
        "views/attendance_sync_log_view.xml",

        #security
        "security/ir.model.access.csv"

    ],
    'external_dependencies': {
        'python': ['pika']
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
}
