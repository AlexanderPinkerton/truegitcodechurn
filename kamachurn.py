import subprocess
import gitcodechurn

command = "git log --format='%aN' | sort -u"

command1 = ["git", "log", "--format='%aN'"]

#process = subprocess.run(command1, stdout=subprocess.PIPE)
#output, error = process.communicate()

authors = subprocess.Popen(command1, stdout=subprocess.PIPE, universal_newlines=True)
sort = subprocess.Popen(["sort", "-u"], stdin=authors.stdout, stdout=subprocess.PIPE, universal_newlines=True)





while True:
    output = sort.stdout.readline()
    print(output.strip())
    # Do something else

    #churner = ["python", "./gitcodechurn.py", "--before=2019-03-01", "--after=2018-11-29", f"--author={output.strip()}", "--dir='.'"]
    #wat = subprocess.Popen(churner, stdout=subprocess.PIPE, universal_newlines=True)

    gitcodechurn.main()


    #return_code = sort.poll()
    #if return_code is not None:
    #    print('RETURN CODE', return_code)
    #    # Process has finished, read rest of the output
    #    for output in sort.stdout.readlines():
    #        print(output.strip())
    #    break



#python ./gitcodechurn.py --before=2019-03-01 --after=2018-11-29 --author="Some author" --dir=/Users/myname/myrepo
