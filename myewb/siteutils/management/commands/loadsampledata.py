from django.core.management.base import NoArgsCommand
from django.core.management import ManagementUtility


class Command(NoArgsCommand):
    help = "Loads all fixtures named sample_data."

    requires_model_validation = False

    def handle_noargs(self, **options):
        # this doesn't load for some reason (models has been submoduled?)
        utility = ManagementUtility(['./manage.py', 'loaddata', 'apps/base_groups/fixtures/sample_data.json'])
        utility.execute()
        
        # and load sample data from all apps
        utility = ManagementUtility(['./manage.py', 'loaddata', 'sample_data'])
        utility.execute()
        
        return 'Sample data loaded.'

