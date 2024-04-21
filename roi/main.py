import os
import nipype.interfaces.fsl as fsl
from nipype import Node, Workflow, MapNode, IdentityInterface, JoinNode
from nipype.interfaces.utility import Function
from nipype.interfaces.io import DataSink
from preprocess.main import PIPELINE_BASE_DIR
import utils
from os.path import join as opj

ROI_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PIPELINE_BASE_DIR = os.path.dirname(ROI_BASE_DIR)

WORKING_DIR_NAME = "workingdir"

WORKING_DIR = opj(ROI_BASE_DIR, WORKING_DIR_NAME)

itersource_node = Node(interface=IdentityInterface(fields=['zfstat_path', 'affine_file']),
                  name="itersource")
itersource_node.synchronize = True # To avoid all permutations of the two lists being run

MNI_template = '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'

fnirt_node = Node(fsl.FNIRT(ref_file=MNI_template, output_type='NIFTI_GZ'), name="fnirt")

roi_extract_node = Node(Function(input_names=['input_nifti', 'roi_num'], output_names=["roi_values"], function=utils.roi_extract), name="roi_extract")

avg_node = Node(Function(input_names=['roi_values'], output_names=["avg"], function=utils.average_roi_values), name="avg")

join_node = JoinNode(Function(input_names=['roi_values', 'avg'], output_names=["output"], function=utils.join_and_format), name="join")

if __name__ == "__main__":
    print(f"pipeline base dir: {PIPELINE_BASE_DIR}")
    print(f"working dir: {WORKING_DIR}")
    print(f"roi base dir: {ROI_BASE_DIR}")
    
    roi_extract_workflow = Workflow(name="roi_extract_workflow", base_dir=ROI_BASE_DIR)
    
    # connect nodes
    roi_extract_workflow.connect([(itersource_node, fnirt_node, [("zfstat_path", "in_file")]),
                                 (fnirt_node, roi_extract_node, [("out_file", "affine_file")]),
                                 (roi_extract_node, avg_node, [("roi_values", "roi_values")]),
                                 (roi_extract_node, join_node, [("roi_values", "roi_values")]),
                                 (avg_node, join_node, [("avg", "avg")])])
    
    # set crash directory
    roi_extract_workflow.config["execution"]["crashdump_dir"] = opj(roi_extract_workflow.config["execution"]["crashdump_dir"], WORKING_DIR_NAME, "crash")

    # write graphs 
    if "--exec-graph" in os.sys.argv:
        roi_extract_workflow.write_graph(graph2use="exec", dotfilename="exec_graph.dot", format="png")    
    roi_extract_workflow.write_graph(graph2use="colored", format="png")


    # if '-y' argument is passed, run the workflow without asking for confirmation
    if "-y" in os.sys.argv:
        s = "yes"
    else:
        s = input("Would you like to run the workflow? (Y/n)")

    if not (s.lower() == "yes" or s.lower() == "y"):
        print("Exiting...")
        exit(0)
        
    run = roi_extract_workflow.run(plugin="MultiProc", plugin_args={"n_procs": 32})