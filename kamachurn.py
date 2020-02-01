import subprocess
import gitcodechurn

command = "git log --format='%aN' | sort -u"

command1 = ["git", "log", "--format='%aN'"]


# gitcodechurn.get_proc_out

#process = subprocess.run(command1, stdout=subprocess.PIPE)
# output, error = process.communicate()

directory = "/Users/alexanderpinkerton/Documents/CryptVFS"
# directory = "."

# authors = gitcodechurn.get_proc_out(command1, directory)
# print(authors)
# print("------")
# sort = gitcodechurn.get_proc_out(["sort", "-u"], directory)
# print(sort)

authors = subprocess.Popen(command1, stdout=subprocess.PIPE, universal_newlines=True, cwd=directory)
sort = subprocess.Popen(["sort", "-u"], stdin=authors.stdout, stdout=subprocess.PIPE, universal_newlines=True, cwd=directory)


names = []


for output in sort.stdout.readlines():
    # print(output.strip())
    names.append(output.strip())


# while True:
#     output = sort.stdout.readline()
#     print(output.strip())
#     # Do something else

#     #churner = ["python", "./gitcodechurn.py", "--before=2019-03-01", "--after=2018-11-29", f"--author={output.strip()}", "--dir='.'"]
#     #wat = subprocess.Popen(churner, stdout=subprocess.PIPE, universal_newlines=True)

#     names.append(output.strip())


#     return_code = sort.poll()
#     if return_code is not None:
#        print('RETURN CODE', return_code)
#        # Process has finished, read rest of the output
#        for output in sort.stdout.readlines():
#            print(output.strip())
#        break


# print(names) 

for name in names:
    
    commits = gitcodechurn.get_commits("2020-03-01", "2018-11-29", name, directory)
    # print(commits)
    # structured like this: files -> LOC
    files = {}

    contribution = 0
    churn = 0

    for commit in commits:
        [files, contribution, churn] = gitcodechurn.get_loc(
            commit,
            directory,
            files,
            contribution,
            churn
        )

    # print files in case more granular results are needed
    print('Name: ', name)
    print('contribution: ', contribution)
    print('churn: ', -churn)


#python ./gitcodechurn.py --before=2019-03-01 --after=2018-11-29 --author="Some author" --dir=/Users/myname/myrepo
