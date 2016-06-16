import os, subprocess, tempfile, base64, time

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tesseract-lambda')
LIB_DIR = os.path.join(SCRIPT_DIR, 'lib')

def ocr(event):
    with tempfile.NamedTemporaryFile() as temp:
        b64 = event['data'].split('base64,')[1]

        temp.write(base64.b64decode(b64))
        temp.flush()

	start = time.clock()

	ocr_name = temp.name
	if event['filename'].split('.')[1] == 'pdf':
	    ocr_name += '.tiff'
	    cmd = 'gs -dNOPAUSE -r720x720 -sDEVICE=tiffg4 -dBATCH -sOutputFile={} {}'.format(
	        ocr_name,
	        temp.name
	    )
	    print cmd
	    try:
	        output = subprocess.check_output(cmd, shell=True)
		print output
	    except subprocess.CalledProcessError as convertE:
	        print convertE.output
	        raise convertE

        cmd = 'LD_LIBRARY_PATH={} TESSDATA_PREFIX={} {}/tesseract {} {}'.format(
            LIB_DIR,
            SCRIPT_DIR,
            SCRIPT_DIR,
            ocr_name,
            temp.name,
        )

        try:
            output = subprocess.check_output(cmd, shell=True)
            ocr_time = time.clock() - start
        except subprocess.CalledProcessError as ocrE:
            print ocrE.output
            raise ocrE

        with open(temp.name+'.txt', 'r+') as outfd:
            ocr = base64.b64encode(outfd.read())

        os.remove(temp.name+'.txt')
        
        ret_name = event['filename'].split('.')[0] + '.txt'

        return {'data':ocr, 'filename':ret_name, 'time':ocr_time}

def handler(conn, event):
    fn = {
        'ocr': ocr
    }[event['op']]

    # run specific handler
    return fn(event)

if __name__ == '__main__':
    with open('pdf-sample.pdf', 'r') as fd:
	b64 = base64.b64encode(fd.read())
    event = {
	'op':'ocr',
	'filename':'pdf-sample.pdf',
	'data':'base64,'+b64
    }
    handler(0, event)