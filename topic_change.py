from fabric import api

import csv
import glob
import os
import re
import time
import util


@api.task
def prepare(output_directory, source_topic, destination_topic):
    """Build CSV files for moving all content.

    :param output_directory: The directory that CSV files should be placed in.

    :param source_topic: The existing topic tag content is tagged to.

    :param source_topic: The new topic tag that content should be tagged to.

    A separate CSV file is created for each app, by running tasks on an
    appropriate backend machine.

    The CSV files are then downloaded to the local directory specified.

    """
    do_prepare(output_directory, source_topic, destination_topic)


def do_prepare(output_directory, source_topic, destination_topic):
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    prepare_publisher_csv(output_directory, source_topic, destination_topic)
    prepare_whitehall_csv(output_directory, source_topic, destination_topic)


@api.task
def process(file_pattern):
    """Process topic change CSVs.

    Processes all CSVs matching the given file pattern glob.  This will apply
    the listed changes to content in whitehall and publisher (updating all the
    appropriate things).

    :param file_pattern: A glob-style pattern used to determine which CSV files
           to process.

    """
    do_process(file_pattern)


def do_process(file_pattern):
    paths_by_app = {}
    for path in glob.glob(file_pattern):
        app = os.path.basename(path).split("_")[0]
        paths_by_app.setdefault(app, []).append(path)

    process_publisher_csvs(paths_by_app.pop("publisher", []))
    process_whitehall_csvs(paths_by_app.pop("whitehall", []))
    if paths_by_app:
        print "WARNING: Ignoring files for unknown apps: %s" % (
            ', '.join(paths_by_app.keys()))


@api.task
def move_in_panopticon(source_topic, destination_topic):
    """Move content tagged in panopticon

    """
    do_move_in_panopticon(source_topic, destination_topic)

def do_move_in_panopticon(source_topic, destination_topic):
    util.use_random_host('class-backend')
    print("\nRetagging content on %s" % (api.env.host_string,))
    util.rake('panopticon', 'move_content_to_new_topic',
              source=source_topic, dest=destination_topic)


@api.task
def delete_topic(old_topic):
    """Delete a topic, causing it to return a 410 gone status.

    """
    do_delete_topic(old_topic)

def do_delete_topic(old_topic):
    util.use_random_host('class-backend')
    print("\nDeleting old topic %s" % (old_topic,))
    util.rake('panopticon', 'specialist_sector_cleanup', SLUG=old_topic)


@api.task
def move_topics(csv_filename, output_directory, action="all"):
    """Apply a set of topic changes from a CSV.

    This takes a CSV which maps from old topic slug to new topic slug, and
    coordinates running all the changes.

    """
    topic_slug_changes = read_topic_slug_changes(csv_filename)
    action = action.lower()

    if action in ["all", "prepare"]:
        if os.path.exists(output_directory):
            print "Output directory already exists"
            print "Aborting, to avoid risk of pulling in unexpected changes."
            exit(1)
        os.makedirs(output_directory)
        for old_slug, new_slug in topic_slug_changes.items():
            do_prepare(output_directory, old_slug, new_slug)

    if action in ["all", "process"]:
        do_process(output_directory + "/*.csv")

    if action in ["all", "panopticon"]:
        for old_slug, new_slug in topic_slug_changes.items():
            move_in_panopticon(old_slug, new_slug)

    if action in ["all", "delete"]:
        for old_slug in topic_slug_changes.keys():
            delete_topic(old_slug)


def read_topic_slug_changes(csv_filename):
    changes = {}
    with open(csv_filename) as fobj:
        reader = csv.reader(fobj)
        headings = [
            heading.lower().strip().replace(' ', '_')
            for heading in reader.next()
        ]
        old_index = headings.index('old_topic_slug')
        new_index = headings.index('new_topic_slug')
        for row in reader:
            changes[row[old_index]] = row[new_index]
    return changes


def slugify(topic):
    return re.sub('[^a-z0-9]', '_', topic.lower())


def build_filename(app, source_topic, destination_topic):
    return '__'.join([
        app,
        slugify(source_topic),
        slugify(destination_topic),
        str(int(time.time())),
    ]) + '.csv'


def prepare_publisher_csv(output_directory, source_topic, destination_topic):
    util.use_random_host('class-backend')
    print("\nFetching publisher change CSV from %s" % (api.env.host_string,))

    filename = build_filename('publisher', source_topic, destination_topic)
    remote_path = '/var/apps/publisher/tmp/%s' % (filename,)
    util.rake('publisher', 'topic_changes:prepare',
              source_topic,
              destination_topic,
              remote_path)
    api.get(remote_path, os.path.join(output_directory, filename))
    api.sudo("rm '%s'" % (remote_path,), user="deploy")


def prepare_whitehall_csv(output_directory, source_topic, destination_topic):
    util.use_random_host('class-whitehall_backend')
    print("\nFetching whitehall change CSV from %s" % (api.env.host_string,))

    filename = build_filename('whitehall', source_topic, destination_topic)
    remote_path = '/var/apps/whitehall/tmp/%s' % (filename,)
    util.rake('whitehall', 'topic_retagging_csv_export',
              SOURCE=source_topic,
              DESTINATION=destination_topic,
              CSV_LOCATION=remote_path,
    )
    api.get(remote_path, os.path.join(output_directory, filename))
    api.sudo("rm '%s'" % (remote_path,), user="deploy")


def process_publisher_csvs(paths):
    util.use_random_host('class-backend')
    for path in paths:
        process_publisher_csv(path)


def process_publisher_csv(path):
    filename = os.path.basename(path)
    print("\nApplying publisher change CSV %s on %s" % (
        filename,
        api.env.host_string,
    ))
    if file_length(path) == 1:
        print("No changes in file - skipping")
        return

    remote_path = '/var/apps/publisher/tmp/%s' % (filename, )
    api.put(path, remote_path, use_sudo=True)
    util.rake('publisher', 'topic_changes:process', remote_path)
    api.sudo("rm '%s'" % (remote_path,))


def file_length(path):
    with open(path) as fobj:
        return len(fobj.readlines())


def process_whitehall_csvs(paths):
    util.use_random_host('class-whitehall_backend')
    for path in paths:
        process_whitehall_csv(path)


def process_whitehall_csv(path):
    filename = os.path.basename(path)
    print("\nApplying whitehall change CSV %s on %s" % (
        filename,
        api.env.host_string,
    ))
    if file_length(path) == 1:
        print("No changes in file - skipping")
        return

    remote_path = '/var/apps/whitehall/tmp/%s' % (filename, )
    api.put(path, remote_path, use_sudo=True)
    util.rake('whitehall', 'process_topic_retagging_csv',
              CSV_LOCATION=remote_path)
    api.sudo("rm '%s'" % (remote_path,))
