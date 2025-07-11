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

    ],
    'external_dependencies': {
        'python': ['pika']
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
