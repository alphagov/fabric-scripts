from fabric.api import *

@task
@hosts('graphite-1.management')
def prune_stale_whisper_files():
    """Delete Whisper files that have not been modified in over 90 days"""
    sudo("find /opt/graphite/storage/whisper -type f -mtime +90 -exec rm {} +")
    sudo("find /opt/graphite/storage/whisper -type d -empty -exec rmdir {} +")
