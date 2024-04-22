from nipype import Node, Function

if __name__ == "__main__":
    # Try to return multiple outputs in a custom Function nipype node
    
    # Create a custom function that returns multiple outputs
    def custom_fnirt(in_file: str, affine_file: str) -> tuple:
        """
        Custom implementation of FNIRT.
        """
        import os        
        
        # Create the output file name
        out_file = os.path.join(os.getcwd(), "warped.nii.gz")
        
        return out_file, "output2"

    # Create a custom Function nipype node
    custom_fnirt_node = Node(Function(input_names=['in_file', 'affine_file'], output_names=["warped_file", "output2"], function=custom_fnirt), name="custom_fnirt")
    custom_fnirt_node.inputs.in_file = "input.nii.gz"
    custom_fnirt_node.inputs.affine_file = "affine.mat"

    def dest_node_func(warped_file: str, output2: str) -> str:
        print(f"warped_file: {warped_file}")
        print(f"output2: {output2}")
        return "output"

    dest_node = Node(Function(input_names=["warped_file", "output2"], output_names=["output"], function=dest_node_func), name="dest_node")

    # create a dummy workflow
    from nipype import Workflow
    wf = Workflow(name="wf")
    
    wf.connect(custom_fnirt_node, "warped_file", dest_node, "warped_file")
    wf.connect(custom_fnirt_node, "output2", dest_node, "output2")        
    
    wf.run()
    