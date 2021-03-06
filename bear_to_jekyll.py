import argparse
import os.path, os
import re
import shutil

import bear
import sys


def title_to_filename(path, title, date):
    """
    We build a simple filename from the title - i.e. "These Cats" becomes "these_cats.md". We do
    not check for existence, as we may be doing an overwrite deliberately.
    """

    title = re.sub('[`~!@#$%^&*():;"<>,./?]', '', title)
    name = date + "-" + re.sub(r'[^a-z0-9]','_',title.lower())
    return os.path.join(path, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Export Bear posts as Jekyll-compatible markdown')
    parser.add_argument('output', type = str,
                        help = 'directory to output to')
    parser.add_argument('--tag', type = str, action='append', help='Tag to export, you can specify multiple times. If no tags are specified all posts will be exported')
    parser.add_argument('--html', action = "store_true", help = "render as html")
    args = parser.parse_args()

    full_path = os.path.join(os.getcwd(), args.output)

    # Check directory exists
    if not os.path.isdir(full_path):
        print("The given output directory {} does not exist".format(full_path))
        sys.exit(1)

    # Open Bear database
    b = bear.Bear()

    # Check tags
    if args.tag:
        notes = []
        for tag in args.tag:
            t = b.tag_by_title(tag)
            if not t:
                print("The given tag '{}' does not exist - note they're case sensitive".format(tag))
                sys.exit(1)
            for note in t.notes():
                notes.append(note)
    else:
        notes = b.notes()

    # Iterate through all notes
    for note in notes:
        # Create a suitable filename
        filename = title_to_filename(full_path, note.title, note.created.strftime('%Y-%m-%d')) + '.md'

        note.text = '\n'.join(note.text.split('\n')[1:])
        note.text = re.sub(r'\[image:', r'![](assets/posts/', note.text)
        note.text = re.sub(r'.png]', r'.png)', note.text) # supports .png only - add formats as needed
        note.text = re.sub(r'\n#public.*', r'', note.text) # removes all lines that begin with #public

        # hacky converter for [[note title]] links
        # changes them to <a href="note link">note title</a>
        # it removes some special characters from the URL
        note.text = re.sub(r'(\[+)(.+)(]])', r'<a href="{{ "\2" | replace: " ", "_" | remove: "(" | remove: ")" | remove: "~" | remove: "!" | remove: "@" | remove: "#" | remove: "$" | remove: "&" | remove: ":" | remove: ";" | remove: "?" | remove: "," | remove: "." | downcase }}">\2</a>', note.text)

        for f in re.findall("](.)", note.text):
            note.text = note.text.replace(f, f.lower())
        # note.text = re.sub(r'()', lowe)

        # <crosssell id="123" selltype="456">

        #               ?(\.[^\.]*)$
        # re.sub(r'(\_a)?\.([^\.]*)$' , r'_suff.\2',"long.file.name.jpg")

        # <a href="https://github.com/bhardin/spotthevuln/blob/gh-pages/_posts/{{ page.date | date: "%Y-%m-%d" }}-{{ page.title | remove: " -" | replace: " ", "-" | downcase }}.md"


        # Write out the post
        with open(filename, 'w', encoding = 'utf8') as f:

            f.write("""---
title: {}
date: {}
tags: [ {} ]
uuid: {}
layout: default
category: blog
---
{}""".format(note.title, note.created.strftime('%Y-%m-%d %H:%M:%S +0000'), ', '.join([t.title for t in note.tags()]), note.id, note.text))

            # Images to copy
            for image in note.images():
                if image.exists():
                    # Figure out target path for image
                    post_path = os.path.join(full_path, image.uri)
                    target_path = post_path.replace("/_posts", "/assets/posts", 1)
                    # Make dir
                    os.makedirs(os.path.dirname(target_path), exist_ok = True)
                    # Copy file
                    shutil.copyfile(image.path, target_path)
