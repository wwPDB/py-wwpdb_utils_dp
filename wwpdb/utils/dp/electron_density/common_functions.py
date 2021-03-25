import shlex

import json
import logging
import os
import shutil
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
        logging.debug(command)
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
            logging.debug('checking for {}'.format(output_file))
            if os.path.exists(output_file):
                logging.debug('file exists')
                return True
            else:
                logging.error('output file missing: {}'.format(output_file))
        else:
            logging.error('command returned non-zero exit status')
    else:
        logging.error('either command or output file not set')

    return False


def convert_mdb_to_binary_cif(node_path,
                              volume_server_query_path,
                              map_id,
                              source_id,
                              mdb_map_path,
                              output_file,
                              working_dir,
                              detail=4):
    query_kind = 'cell'
    map_file_name = '{}_{}-{}_d{}.bcif'.format(map_id, source_id, query_kind, detail)
    if not working_dir:
        working_dir = os.getcwd()
    temp_out_file = os.path.join(working_dir, map_file_name)
    json_filename = 'conversion.json'
    json_content = [{
        "source": {
            "filename": mdb_map_path,
            "name": map_id,
            "id": source_id
        },
        "query": {
            "kind": query_kind
        },
        "params": {
            "detail": detail,
            "asBinary": True
        },
        "outputFolder": working_dir,
        "outputFilename": temp_out_file
    }]
    if working_dir:
        working_json = os.path.join(working_dir, json_filename)
    else:
        working_json = json_filename
    with open(working_json, 'w') as out_file:
        json.dump(json_content, out_file)
    command = "{} {} --jobs {}".format(node_path, volume_server_query_path, working_json)
    ret = run_command_and_check_output_file(command=command,
                                            process_name='mdb_to_binary_cif',
                                            workdir=working_dir,
                                            output_file=temp_out_file
                                            )
    if ret:
        output_folder = os.path.dirname(output_file)
        if output_folder:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
        shutil.copy(temp_out_file, output_file)
        logging.debug('output file {}'.format(output_file))
        return True
    return False
