# Run python get.py
# Get the rules from profiles
import os, glob

if __name__ == "__main__":

    current_dir = os.path.abspath( __file__ )[:-6]
    dir = current_dir + '../data/app_profiles'
    all_categories = []
    os.chdir(dir)
    
    fw = open(current_dir + 'extra_translations.py', 'w')
    fw.write("%s\n" % 'import gettext')
    fw.write("%s\n" % 'from gettext import gettext as _')
    fw.write("%s\n" % 'gettext.textdomain("gufw")')
    fw.write("%s\n" % 'if __name__ == "__main__":')
    for file in glob.glob("*.*"):
        # Extract data for each service
        title = ''
        description = ''
        ports = ''
        categories = ''
        warning = ''
        f = open(file, 'r')
        for line in f:
            line = line.replace('\n', '')
            if 'title=' in line:
                title = line.replace('title=', '')
            if 'description=' in line:
                description = line.replace('description=', '')
            if 'ports=' in line:
                ports = line.replace('ports=', '')
            if 'categories=' in line:
                categories = line.replace('categories=', '')
            if 'warning=' in line:
                warning = line.replace('warning=', '')

            # Done
            if title and description and ports and categories:
                fw.write("    print(_(\"%s\"))\n" % title)
                fw.write("    print(_(\"%s\"))\n" % description)
                if all_categories.count(categories) == 0:
                    fw.write("    print(_(\"%s\"))\n" % categories)
                    all_categories.append(categories)
                if warning:
                    fw.write("    print(_(\"%s\"))\n" % warning)
                title = ''
                description = ''
                ports = ''
                categories = ''
                warning = ''
    fw.write("    print(_(\"%s\"))\n" % 'Authentication is required to run the Firewall Configuration')
    fw.write("    print(_(\"%s\"))\n" % 'Firewall Configuration')
    fw.write("    print(_(\"%s\"))\n" % 'An easy way to configure your firewall')
    fw.close()
