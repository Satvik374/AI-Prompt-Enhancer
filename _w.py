import base64,sys
open(sys.argv[2],"wb").write(base64.b64decode(sys.argv[1]))
