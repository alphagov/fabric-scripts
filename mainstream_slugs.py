from fabric.api import task
import util


@task
def change(old_url, new_url):
    """Change a mainstream slug. Usage: fab integration mainstream_slugs.change:old_slug=/old-slug,new_slug=/new-slug"""
    util.use_random_host('class-backend')
    util.rake('panopticon', 'delete_mainstream_slug_from_search', old_url)
    util.rake('publisher', 'update_mainstream_slug', old_url, new_url)
