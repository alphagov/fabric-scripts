from fabric.api import *

@task
@roles('class-rabbitmq')
def status():
    """Output the RabbitMQ cluster status"""
    sudo('rabbitmqctl cluster_status', warn_only=True)
