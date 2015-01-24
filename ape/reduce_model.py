from fsm import utilities
import sys

dest_event = sys.argv[1]
dot_file = sys.argv[2]
reduced_dot_file = sys.argv[3]

model = utilities.dot_to_fsm(dot_file)
utilities.reduce(model, dest_event)
utilities.fsm_to_dot(model, reduced_dot_file)
