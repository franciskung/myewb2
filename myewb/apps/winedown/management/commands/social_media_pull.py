from django.core.management.base import NoArgsCommand, CommandError

from winedown import twitter

class Command(NoArgsCommand):
    help = "Loads social media content into myEWB"

    requires_model_validation = False
    can_import_settings = True

    def handle_noargs(self, **options):
        twitter.load_tweets()
        
