# AUTOGENERATED! DO NOT EDIT! File to edit: 01_convert_time_log.ipynb (unless otherwise specified).

__all__ = ['trace_log', 'format_value', 'strip_extra_EnmacClientTime_elements', 'unix_time_milliseconds', 'parse_dt',
           'parse_dt_to_milliseconds', 'parse_httpd_dt', 'parse_httpd_dt_to_milliseconds', 'match_last2digits',
           'parse_timing_log', 'parse_log_line', 'parse_log_line_to_dict', 'parse_httpd_log', 'log_re', 'request_re',
           'parse_httpd_log_file', 'parse_timing_log_file']

# Cell
import xml.etree.ElementTree as ET

import tempfile
import sys

import numbers
import decimal

class trace_log():
    def __init__(self,fp_output):
        self.outfile = fp_output
        self.outfile.write('{ "traceEvents": \n')
        self.outfile.write('[')

    def write_element(self, event_type, name, categories, pid,tid, ts,additional_args=None,dur=None):
        ''' {"name": "Asub", "cat": "PERF", "ph": "B", "pid": 22630, "tid": 22630, "ts": 829}'''

        line = '"name": "%s", "cat": %s, "ph": "%s", "pid": %s, "tid": %s, "ts": %s,' %(name,categories,event_type,pid,tid,ts)
        if dur is not None:
            line+= format_value('dur',dur) + ','
        if additional_args is not None and len(additional_args) > 0:
            line += format_value('args',additional_args) + ','
        self.outfile.write('{'+line+'},\n')

    def write_start_element(self, name, categories, pid,tid, ts,additional_args=None):
        self.write_element('B',name,categories,pid,tid,ts,additional_args)

    def write_end_element(self, name, categories, pid,tid, ts):
        self.write_element('E',name,categories,pid,tid,ts)

    def write_duration_event(self, name, categories, pid,tid, ts,dur, additional_args=None):
        self.write_element('X',name,categories,pid,tid,ts,additional_args, dur)

    def close(self):
        self.outfile.write('],\n')
        self.outfile.write(''' "displayTimeUnit": "ms",
 "systemTraceEvents": "SystemTraceData",
 "otherData": { "version": "PowerOn Client Trace"},
}
''')
        self.outfile.close()


def format_value(name, value):
    ''' takes name and value and returns a string for the value element'''
    formatted_string = ''
    if name is not None:
        formatted_string += '"%s": '%name
    if isinstance(value, numbers.Number):
        formatted_string += '%s'%value
    elif isinstance(value, dict):
        formatted_string +=  '{'
        sep = ''
        for key1,value1 in value.items():
            formatted_string += sep + format_value(key1,value1)
            sep = ','
        formatted_string += '}'
    elif isinstance(value, list):
        formatted_string += '['
        sep = ''
        for item in value:
            formatted_string += sep + format_value(None,item)
            sep = ','
        formatted_string += ']'
    else:
        formatted_string += '"%s"' %value

    return formatted_string


# Cell

def strip_extra_EnmacClientTime_elements(filename,fp):
    ''' since we may have multiple EnmacClientTiming tags in the document we need to strip them out and add one at the end'''

    fp.write("<EnmacClientTiming>\n")

    if sys.version_info[0] < 3:
        file = open(filename, 'r')
    else:
        file = open(filename, 'r', encoding='utf8')

    if file is None:
        print('Error opening file: %s' %filename)
        return
    for line in file:
        l = line.rstrip()
        if l == '<EnmacClientTiming>' or l == '</EnmacClientTiming>':
            continue
        fp.write(line)

    fp.write("</EnmacClientTiming>\n")



# Cell

import datetime
import re

if sys.version_info[0] < 3:
    epoch = datetime.datetime(1970, 1, 1)
else:
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
match_last2digits = re.compile(r"(\d\d)$", re.IGNORECASE)

#epoch = datetime.datetime.fromtimestamp(0,datetime.timezone.utc) #

def unix_time_milliseconds(dt):
    return (dt - epoch).total_seconds() * 1000.0

def parse_dt(time_str):
    ''' Parse string in format 2021-12-07T08:51:46.479299+00:00
    return datetime'''

    if sys.version_info[0] < 3:
        time_str = time_str[:-6]
        return datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')
    else:
        return datetime.datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=datetime.timezone.utc)

    return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f%z")

def parse_dt_to_milliseconds(time_str):
    return unix_time_milliseconds(parse_dt(time_str))


def parse_httpd_dt(time_str):
    ''' parse a date time string which is in the format
    25/Sep/2002:14:04:19 +0200
    '''

    if sys.version_info[0] < 3:
        time_str = time_str[:-6]
        return datetime.datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S')
    else:
        time_str =match_last2digits.sub(":\\1", time_str)

        return datetime.datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S %z').replace(tzinfo=datetime.timezone.utc)

def parse_httpd_dt_to_milliseconds(time_str):
    ''' parse a datetime in the format:
    03/Dec/2021:09:36:46 +0200'''
    return unix_time_milliseconds(parse_httpd_dt(time_str))






# Cell

class parse_timing_log():

    def __init__(self, fp_input, fp_output):

        self.parse_functions = {
        'Timing' : self.skip_element,
        'Parameters' : self.skip_element,
        'DataTables' : self.skip_element,
        'HttpWebRequest' : self.parse_HttpWebRequest,
        'CreateDataSet' : self.parse_CreateDataSet,
        'FormAction' : self.parse_FormAction,

        }

        self.fp = fp_input
        self.fp_output = fp_output
        #self.elements = []
        #self.path_list = []
        self.level = 0
        self.t = trace_log(fp_output)

        self.parse2()

    def skip_element(self, elment):
        return 0


    def parse_datatables_element(self, elem):
        ''' Parse element datatables which looks like:
        <DataTables name="AvailableResources" tables="5" error="false">
            <DataTable name="AVAILABLERESOURCES" rows="7"/>
            <DataTable name="CONTACTDETAILS" rows="7"/>
            <DataTable name="RESOURCEZONES" rows="0"/>
            <DataTable name="ASSIGNED_INCIDENTS" rows="0"/>
            <DataTable name="RESOURCE_OZ_ASSOCIATIONS" rows="2"/>
        </DataTables>
    return a list of date tables as arguments...'''
        datatables  = { 'name': elem.attrib['name'], 'number_of_tables': elem.attrib['tables'], 'error': elem.attrib['error'] }

        tables = []
        for child in elem:
            tables.append({ 'name':child.attrib['name'], 'rows':child.attrib['rows'] })
        datatables['tables'] = tables
        return datatables

    def parse_parameter_element(self, element):
        ''' Parse element parameter which looks like:
        <Parameters postSize="105">
            <Parameter name="searchlon" value="28.020557"/>
            <Parameter name="positionupdatewithinmins" value="30"/>
            <Parameter name="radiusinmiles" value="False"/>
            <Parameter name="searchradius" value="10"/>
            <Parameter name="searchlat" value="-26.033414"/>
        </Parameters>
        returns a list of parameters as arguments...'''
        parameters = {'postSize': element.attrib['postSize']}
        params = {}
        for child in element:
            params[child.attrib['name']] = child.attrib['value']
            #params.append({'name': child.attrib['name'], 'value': child.attrib['value']})
        parameters['params'] = params
        return parameters

    def get_end_time(self, element):
        ''' gets the timing element in element and returns the ms'''
        timing = element.find('Timing')
        if timing is None:
            print('no timing element found')
            return None
        ts = timing.attrib["end"]
        ms = parse_dt_to_milliseconds(ts)

        if timing.attrib["thread"] != element.attrib["thread"]:
            print('missmatched timing threads ??')
        return ms

    def parse_HttpWebRequest(self,elem):
        ''' Parse element HttpWebRequest which looks like:

        <HttpWebRequest start="2021-12-07T17:46:43.910299+00:00" client="hydrogen-w11" thread="282" method="POST" uri="https://trn1nms/enmac/resources/available" status="OK" serverElapsed="0.33" serverCPU="0.0257">
        <Parameters postSize="105">
            <Parameter name="searchlon" value="28.020557"/>
            <Parameter name="positionupdatewithinmins" value="30"/>
            <Parameter name="radiusinmiles" value="False"/>
            <Parameter name="searchradius" value="10"/>
            <Parameter name="searchlat" value="-26.033414"/>
        </Parameters>
        <Timing thread="282" end="2021-12-07T17:46:45.688867+00:00" elapsed="1.78"/>
        </HttpWebRequest>

        '''
        name = elem.attrib["uri"]
        categories = '"HttpWebRequest"'
        pid = 1
        tid = elem.attrib["thread"]
        ts = elem.attrib["start"]
        ms = parse_dt_to_milliseconds(ts)

        parameters = elem.find('Parameters')
        p = self.parse_parameter_element(parameters)
        additional_args = {
                    'parameters': p,
                    'start':ts,
                    'client':elem.attrib["client"],
                    'method':elem.attrib["method"],
                    'status':elem.attrib["status"],
                    'serverElapsed': float(elem.attrib["serverElapsed"]),
                    'serverCPU': float(elem.attrib["serverCPU"]) }


        self.t.write_start_element(name,categories ,pid,tid,ms,additional_args)

        self.parse_elements(elem)
        ms = self.get_end_time(elem)
        self.t.write_end_element(name,categories ,pid,tid,ms)
        return 0


    def parse_CreateDataSet(self,elem):
        '''
        Parse element CreateDataSet which looks like:
        <CreateDataSet start="2021-12-07T17:50:36.520401+00:00" client="hydrogen-w11" thread="273" path="/enmac/swex/outages">
        ....
        <DataTables name="AvailableResources" tables="5" error="false">
        <DataTable name="AVAILABLERESOURCES" rows="7"/>
        <DataTable name="CONTACTDETAILS" rows="7"/>
        <DataTable name="RESOURCEZONES" rows="0"/>
        <DataTable name="ASSIGNED_INCIDENTS" rows="0"/>
        <DataTable name="RESOURCE_OZ_ASSOCIATIONS" rows="2"/>
        </DataTables>
         <Timing thread="282" end="2021-12-07T17:46:45.688867+00:00" elapsed="1.78"/>
        </CreateDataSet>
        '''
        name = elem.attrib["path"]
        categories = '"CreateDataSet"'
        pid = 1
        tid = elem.attrib["thread"]
        ts = elem.attrib["start"]
        ms = parse_dt_to_milliseconds(ts)

        datatables = elem.find('DataTables')
        dt = self.parse_datatables_element(datatables)

        additional_args = {
                    'datatables': dt,
                    'start':ts,
                    'client':elem.attrib["client"]}
        self.t.write_start_element(name,categories ,pid,tid,ms,additional_args)

        self.parse_elements(elem)

        ms = self.get_end_time(elem)
        self.t.write_end_element(name,categories ,pid,tid,ms)
        return 0

    def parse_FormAction(self,elem):
        '''
        <FormAction start="2021-12-07T17:46:23.903476+00:00" client="hydrogen-w11" thread="18"
        form="MainForm" action="SendNetServerMessage(&#39;MD_SET_PIPE_MESSAGE_FILTER&#39;, &#39;135&#39;)">>
        '''
        name = elem.attrib["action"]
        form = elem.attrib["form"]
        categories = '"FormAction,%s"'%form
        pid = 1
        tid = elem.attrib["thread"]
        ts = elem.attrib["start"]
        ms = parse_dt_to_milliseconds(ts)

        additional_args = {
                    'start':ts,
                    'client':elem.attrib["client"],
                    'form': form}
        self.t.write_start_element(name,categories ,pid,tid,ms,additional_args)


        self.parse_elements(elem)
        ms = self.get_end_time(elem)
        self.t.write_end_element(name,categories ,pid,tid,ms)

        return 0

    def parse_elements(self, elem):
        for child in elem:
            func= self.parse_functions.get(child.tag,lambda :-1)
            if func(child) <0:
                print('Unknown tag: elem.tag')

    def parse2(self):
        tree = ET.parse(self.fp)
        root = tree.getroot()
        self.parse_elements(root)
        self.t.close()



# Cell

# [03/Dec/2021:09:36:46 +0200] 172.17.106.244 "devwks2" "POST /enmac/login/hostDetails HTTP/1.1" 200 652 pid:1980400 time:12680 +
# [03/Dec/2021:09:36:47 +0200] 172.17.106.244 "-" "GET /enmac/packages/restrict_new_clients HTTP/1.1" 404 196 pid:1980400 time:317 +
# [03/Dec/2021:10:04:56 +0200] 172.17.106.244 "devwks2" "POST /enmac/login/hostDetails HTTP/1.1" 200 655 pid:2020510 time:9657 +
# [03/Dec/2021:10:04:56 +0200] 172.17.106.244 "-" "GET /enmac/packages/restrict_new_clients HTTP/1.1" 404 196 pid:2020510 time:243 +
# [03/Dec/2021:15:19:04 +0200] 172.17.106.244 "devwks2" "POST /enmac/login/hostDetails HTTP/1.1" 200 655 pid:2047496 time:11086 +
# [03/Dec/2021:15:19:04 +0200] 172.17.106.244 "-" "GET /enmac/packages/restrict_new_clients HTTP/1.1" 404 196 pid:2047496 time:278 +
# [03/Dec/2021:16:00:04 +0200] 172.17.106.244 "devwks2" "POST /enmac/login/hostDetails HTTP/1.1" 200 655 pid:2020512 time:9956 +
# [03/Dec/2021:16:00:04 +0200] 172.17.106.244 "-" "GET /enmac/packages/restrict_new_clients HTTP/1.1" 404 196 pid:2020512 time:238 +
# [03/Dec/2021:17:57:48 +0200] 172.31.243.25 "hydrogen-w11" "POST /enmac/login/hostDetails HTTP/1.1" 200 655 pid:2020514 time:209610 +



#log_re = re.compile('\[(.*?)\] ([(\d\.)]+) "(.*?)" "(.*?)" (\d+) (\d+) pid:(\d+) time:(\d+) ([+-]+)')
log_re = re.compile('\[(.*?)\] ([(\d\.)]+) "(.*?)" "(.*?)" (\d+) (\d+) pid:(\d+) time:(\d+) ([+-]+)')
def parse_log_line(line):
    ''' parse an apache httpd log line. Given the line, return the date, ip,request, response_code,length'''
    matches = log_re.match(line).groups()
    return matches

request_re = re.compile('^(.*?) (.*?) (.*?$)')
def parse_log_line_to_dict(line):
    #print(line)
    #continue
    l = {}
    matches = parse_log_line(line)
    #matches = log_re.match(line).groups()
    dt_str = matches[0]
    l['dt_str'] = dt_str
    l['ts'] = parse_httpd_dt_to_milliseconds(dt_str)
    l['ip_addr'] = matches[1]
    l['client_name'] = matches[2]
    request = matches[3]
    l['response_code'] = matches[4]
    l['response_length'] = int(matches[5])
    l['pid'] = matches[6]
    duration_microseconds = int(matches[7])
    l['duration_milliseconds'] = duration_microseconds / 1000.0

    req_match = request_re.match(request).groups()
    l['method'] = req_match[0]
    l['name'] = req_match[1]
    l['protocol'] = req_match[2]
    #print(f'{dt_str} {ip_addr} {request} {response_code}  {response_length}  {pid} {duration}' )
    return l



class parse_httpd_log():

    def __init__(self, fp_input,fp_output):

        self.fp_input = fp_input
        self.fp_output = fp_output
        self.t = trace_log(fp_output)
        self.process_log()


    def process_log(self):
        for line in self.fp_input:
            l = parse_log_line_to_dict(line)
            categories='"httpd"'
            additional_args = {
                    'start':l['dt_str'],
                    'client':l['ip_addr'],
                    'client_name':l['client_name'],
                    'resp_code': l['response_code'],
                    'resp_len': l['response_length']}
            self.t.write_duration_event(l['name'], categories, 1,l['pid'], l['ts'],l['duration_milliseconds'], additional_args)
        self.t.close()

# Cell
def parse_httpd_log_file(input_filename,output_filename,stdout):
    ''' pase the httpd acces log `input_filename` ,
    if `stdout` is set output is send to stdout,
    else if 'output_filename is not set output is saved to `inputfilename` with end changed to json
    otherwise outpuut is saved to `output_filename`'''

    fp = open(input_filename)

    if stdout:
        fo = sys.stdout
    elif output_filename == '':
        outfilename =  os.path.splitext(input_filename)[0] + '.json'
        fo = open(outfilename,'w')
    else:
        outfilename = output_filename
        fo = open(outfilename,'w')

    parse_httpd_log(fp,fo)


def parse_timing_log_file(input_filename, output_filename, preprocess, stdout  ):
    ''' parse the `input_filename`, if the `preprocess` flag is set then it runs the preprocess
    which strips out extra xml tags (and makes it a lot slower since it creates a tmp file,
    if stdout is set then output is streamed there
    if `output_filename` is empty then it outputs to same name as input but with end changed to json'''
    tmp_file = ''

    if preprocess :
        tmp_file = '/tmp/cronos_' + str(random.randint(1, 1000000)) + '.tmp'
        fp = open(tmp_file, 'w+')
        strip_extra_EnmacClientTime_elements(input_filename,fp)
        fp.close()
        fp = open(tmp_file, 'r')
    else:
        fp = open(input_filename)


    if stdout:
        fo = sys.stdout
    elif output_filename == '':
        outfilename =  os.path.splitext(input_filename)[0] + '.json'
        fo = open(outfilename,'w')
    else:
        outfilename = output_filename
        fo = open(outfilename,'w')


    parse_timing_log(fp,fo)
    fo.close()
    fp.close()

    if tmp_file != '':
        os.remove(tmp_file)

# Cell
try: from nbdev.imports import IN_NOTEBOOK
except: IN_NOTEBOOK=False

if __name__ == "__main__" and not IN_NOTEBOOK:
    import argparse
    import os
    import sys
    import random

    ap = argparse.ArgumentParser(description='''Parse ADMS Client Timing Log into event time format, The output file can be viewed in https://ui.perfetto.dev/.
    Source and doc for this utility can be found at https://github.com/3ideas/cronos
    Copyright 3ideas Solutions Ltd ''')

    ap.add_argument('-p', '--nopreprocess', required=False,
                    help="don't preprocess the file to strip out extra EnmacClientTiming tags in the file", default=True, action='store_false')
    ap.add_argument("-f", "--file", required=False, help="client timing log file to parse to generate timing log file from ", default='')
    ap.add_argument("-a", "--httpd_logfile", required=False, help="httpd_logfile  to parse to generate timing log file from ", default='')
    ap.add_argument("-o", "--output", required=False, help="output file name",default = '')
    ap.add_argument("-s","--stdout", required=False, help="print to stdout",default = False, action='store_true')

    args = vars(ap.parse_args())



    if args['file'] != '':
        parse_timing_log_file(args['file'],args['output'],args['nopreprocess'],args['stdout'] )

    if args['httpd_logfile'] != '':
        parse_httpd_log_file(args['httpd_logfile'],args['output'],args['stdout'])



