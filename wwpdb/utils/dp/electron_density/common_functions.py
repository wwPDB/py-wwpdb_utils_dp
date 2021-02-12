import shlex

import json
import logging
import os
import subprocess


def run_command(command, process_name, workdir=None):
    """
    run a command and check the output
    :param str command: the command to be run
    :param str process_name: a name for the process
    :param str None workdir: a path or None for a working directory
    :return bool: True if exit status is zero, False otherwise
    """
    try:
        command_list = shlex.split(command)
        if workdir and workdir is not None:
            process = subprocess.Popen(command_list, cwd=workdir)
        else:
            process = subprocess.Popen(command_list)
        out, err = process.communicate()
        if out:
            logging.info(out)
        if err:
            logging.error(err)
        rc = process.returncode
        if rc != 0:
            logging.error('process failed: {}'.format(process_name))
            return False
        logging.info('process worked: {}'.format(process_name))
        return True
    except Exception as e:
        logging.error(e)
    return False


def run_command_and_check_output_file(command, process_name, output_file, workdir=None):
    """
    run a command and check the output file exists
    :param str command: the command to be run
    :param str None workdir: path or None
    :param str process_name: a name for the process
    :param str output_file: the output file to check for
    :return bool: True if the command exits with status 0 and the output file exists, False otherwise
    """
    if command and output_file:
        ret = run_command(command=command, workdir=workdir, process_name=process_name)
        if ret:
            if os.path.exists(output_file):
                return True

    return False


def convert_mdb_to_binary_cif(map_id, source_id, mdb_map_path, output_folder, output_file, working_dir, detail=4):
    json_filename = 'conversion.json'
    json_content = [{
        "source": {
            "filename": mdb_map_path,
            "name": map_id,
            "id": source_id
        },
        "query": {
            "kind": "cell"
        },
        "params": {
            "detail": detail,
            "asBinary": True
        },
        "outputFolder": output_folder,
        "outputFilename": output_file
    }]
    working_json = os.path.join(working_dir, json_filename)
    with open(working_json, 'w') as out_file:
        json.dump(json_content, out_file)
    command = "volume-server-query --jobs {}".format(working_json)
    return run_command_and_check_output_file(command=command,
                                             process_name='mdb_to_binary_cif',
                                             workdir=working_dir,
                                             output_file=output_file
                                             )
