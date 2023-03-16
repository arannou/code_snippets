# reference
en_file = 'src/assets/i18n-en.json'

# other languages
fr_file = 'src/assets/i18n-fr.json'
other_languages = [fr_file]

# where to look for text in the app
all_html_files = "src/app/**/*.html"
all_ts_files = "src/app/**/*.ts"

# tags content that should not be translated
exclude_tags = ['mat-icon']

# entries that are not detected by script as used in the app
unused_exceptions = ['modal.ruleInfo.qRadarStateSwitchDisable',
                     'modal.ruleInfo.qRadarStateSwitchEnable']

# files that must be excluded from translation (will raise no error)
excluded_files = [
    'src/app/about/privacy/privacy.component.html',
    'src/app/about/gtc/gtc.component.html',
    'src/app/about/disclaimer/disclaimer.component.html'
]
