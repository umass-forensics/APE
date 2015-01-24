__author__ = 'wallsr'

import sys

from optparse import OptionParser

from fsm import utilities
from ape import decoder, log


def find_paths_from_partial(args):
    log('Trying to find paths!')

    #load in the model
    model = utilities.dot_to_fsm(args["model"])

    log(str(model))

    #remove skip states
    for event in args["skip_events"]:
        states = utilities.states_by_event(model, event)
        for state in states:
            log('Removing all %s events' %event)
            model.remove_state(state)

    log(str(model))

    #remove states that are now unreachable from the start
    model = utilities.remove_unreachable_states(model)

    paths = []

    #find paths
    event_str = ','.join(args["partial_path"])
    log('Looking for paths like %s' %event_str)

    new_paths = utilities.get_event_paths(model, args["partial_path"])

    if new_paths:
        paths.extend(new_paths)

    log('Found %d paths.' %len(paths))
    for path in paths:
        print path


def main():
    usage = 'usage: %prog [options]'

    parser = OptionParser(usage=usage)

    parser.add_option('-i', '--input_file', action='store', type='string',
                      dest='input_file', default=None,
                      help='JSON dictionary for the input file')
    parser.add_option('-m', '--input_model', action='store', type='string',
                      dest='input_model', default=None,
                      help='Model dot file')

    options, args = parser.parse_args()

    input_json = ""

    if options.input_file:
        log('Using input file %s' %options.input_file)
        f = open(options.input_file, 'r')
        file_lines = f.readlines()
        # We need to join all the lines (sans \n) into a single string
        input_json = ''.join([line.strip() for line in file_lines])
    else:
        input_json = sys.stdin.read()

        if len(input.strip()) == 0:
            exit(1)

    try:
        print input_json
        input_list = decoder.decode(input_json)
    except ValueError as e:
        log('Unable to read the input JSON.')
        sys.stderr.write(e.message + '\n')
        exit(1)

    import ape_analyze

    for test in input_list:
        if options.input_model:
            test["model"] = options.input_model

        method = getattr(ape_analyze, test['method'])
        method(test)




if __name__ == '__main__':
    main()