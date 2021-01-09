'''
Author: Francis Laclé, Alexander Pinkerton
License: MIT
Version: 0.1

Script to compute "true" code churn of a Git repository.

Code churn has several definitions, the one that to me provides the
most value as a metric is:

"Code churn is when an engineer
rewrites their own code in a short period of time."

Reference: https://blog.gitprime.com/why-code-churn-matters/

This script looks at a range of commits per author. For each commit it
book-keeps the files that were changed along with the lines of code (LOC)
for each file. LOC are kept in a sparse structure and changes per LOC are taken
into account as the program loops. When a change to the same LOC is detected it
updates this separately to bookkeep the true code churn.

Result is a print with aggregated contribution and churn per author for a
given time period.

Tested with Python version 3.5.3 and Git version 2.20.1

'''

# Usage: python gitcodechurn.py --config <configfile.json> --before=2020-05-30 --after=2020-05-20 --chart

import subprocess
import shlex
import os
import argparse
import datetime
import json

import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(
        description = 'Compute true git code churn (for project managers)'
    )
    parser.add_argument(
        '--before',
        type = str,
        help = 'before a certain date, in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--after',
        type = str,
        help = 'after a certain date, in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--author',
        type = str,
        help = 'author string (not committer). Use \'ALL\' for all authors'
    )
    parser.add_argument(
        '--dir',
        type = str,
        help = 'Git repository directory'
    )
    parser.add_argument(
        '--config',
        type = str,
        help = 'File containing various configuration information.'
    )
    parser.add_argument(
        '--chart',
        dest = "chart",
        action = "store_true",
        help = 'Show the churn chart.'
    )

    args = parser.parse_args()

    if not (args.author or args.config):
        parser.error('No action requested, add --author or --authorFile')

    before = args.before
    after = args.after
    author = args.author
    dir = args.dir
    configFile = args.config

    agg_results = {}
    repositories = None

    # if a config file was provided
    if configFile:
        # Parse the data in the authorFile
        with open(configFile) as json_file:
            configData = json.load(json_file)
            authorData = configData.get("aliasMap", None)
            repositories = configData.get("repositories", None)

        if repositories:
            # Clone each repository and then brng them up to date
            for repo in repositories:
                # If the repo does not exist, clone it
                directory = repo.split("/")[1].replace(".git","")
                if not os.path.isdir(directory):
                    command =  f'git clone {repo}'
                    print("Cloning repository: ", repo, command, "\n")
                    out = get_proc_out(command, ".").splitlines()
                else:
                    # otherwise, ensure it is up to date.
                    command = 'git pull'
                    print("Bringing repo up to date", repo)
                    out = get_proc_out(command, directory).splitlines()
                
                # Calculate the churn for the repo and aggregate into total
                repo_results = get_churn_for_repo(before, after, directory, authorData=authorData)
                for alias in repo_results:
                    # Get the existing totals, if any
                    existing = agg_results.get(alias, None)
                    repo_total = repo_results[alias]
                    if existing:
                        # add em up
                        agg_results[alias]['churn'] += repo_total['churn']
                        agg_results[alias]['contribution'] += repo_total['contribution']
                    else:
                        agg_results[alias] = repo_total

    # If there was a specified author
    elif author == "ALL":
        authors = get_authors(dir)
        for name in authors:
            print("Calculating churn for ", name)
            name = name.replace("'", "")
            data = calc_churn(before, after, name, dir)
            if(data["churn"] != 0 or data["contribution"] !=0 ):
                del data['name']
                agg_results[name] = data
    else:
        data = calc_churn(before, after, author, dir)
        del data['name']
        agg_results[author] = data

    if not repositories:
        repositories = [dir]
        print(repositories)
    
    repostr = "\n".join(repositories)
    
    if args.chart == True:
        show_chart(agg_results, before, after, repostr)

    print(agg_results)

def get_churn_for_repo(before, after, directory, authorData=None):
    
    results = {}

    print(f"Calculating churn for {directory}")

    if authorData:
        for name, aliases in authorData.items():
            print("Calculating churn for ", name)
            total_contributions = 0
            total_churn = 0

            for alias in aliases:
                try:
                    data = calc_churn(before, after, alias, directory)
                    if(data["churn"] != 0 or data["contribution"] !=0 ):
                        print("\t", alias, data["contribution"], data["churn"])
                        total_contributions += data["contribution"]
                        total_churn += data["churn"]
                except UnicodeDecodeError as e:
                    print("Failed to calculate churn for ", alias, e)
                
            if(total_churn != 0 or total_contributions !=0):
                results[name] = {"churn":total_churn, "contribution":total_contributions}
        
    else:
        # default to all authors?
        pass
        
    return results


def show_chart(results, before, after, directory):
    x = [ k for k,v in results.items() ]
    y_1 = [ v["contribution"] for k,v in results.items() ]
    y_2 = [ v["churn"] for k,v in results.items() ]

    fig, ax = plt.subplots(num="Code Churn")
    ax.set_title("Repositories\n" + directory + "\n\n" + after + " to " + before)
    ax.set_xlabel('Author')
    ax.set_ylabel('Contributions / Churn')

    ax.bar(x, y_1, color=(122/255, 219/255, 163/255, 0.8))
    ax.bar(x, y_2, color=(252/255, 97/255, 90/255, 0.8))
    ax.axhline(linewidth=1, color='gray')

    # Formatting x labels
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.show()

def calc_churn(before, after, name, dir):
   
    commits = get_commits(before, after, name, dir)

    # structured like this: files -> LOC
    files = {}
    contribution = 0
    churn = 0

    for commit in commits:
        [files, contribution, churn] = get_loc(
            commit,
            dir,
            files,
            contribution,
            churn
        )
    
    return {"name":name, "contribution":contribution, "churn":-churn}

def get_authors(directory):
    # Get all of the authors for this repository
    authors = subprocess.Popen(["git", "log", "--format='%aN'"], stdout=subprocess.PIPE, universal_newlines=True, cwd=directory)
    # Sort and remove duplicates
    sort = subprocess.Popen(["sort", "-u"], stdin=authors.stdout, stdout=subprocess.PIPE, universal_newlines=True, cwd=directory)
    names = []
    for output in sort.stdout.readlines():
        names.append(output.strip())

    return names

def get_loc(commit, dir, files, contribution, churn):
    # git show automatically excludes binary file changes
    command = 'git show --format= --unified=0 --no-prefix ' + commit
    results = get_proc_out(command, dir).splitlines()
    file = ''
    loc_changes = ''

    # loop through each row of output
    for result in results:
        new_file = is_new_file(result, file)
        if file != new_file:
            file = new_file
            if file not in files:
                files[file] = {}
        else:
            new_loc_changes = is_loc_change(result, loc_changes)
            if loc_changes != new_loc_changes:
                loc_changes = new_loc_changes
                locc = get_loc_change(loc_changes)
                for loc in locc:
                    if loc in files[file]:
                        files[file][loc] += locc[loc]
                        churn += abs(locc[loc])
                    else:
                        files[file][loc] = locc[loc]
                        contribution += abs(locc[loc])
            else:
                continue
    return [files, contribution, churn]

# arrives in a format such as -13 +27,5 (no decimals == 1 loc change)
# returns a dictionary where left are removals and right are additions
# if the same line got changed we subtract removals from additions
def get_loc_change(loc_changes):
    # removals
    left = loc_changes[:loc_changes.find(' ')]
    left_dec = 0
    if left.find(',') > 0:
        comma = left.find(',')
        left_dec = int(left[comma+1:])
        left = int(left[1:comma])
    else:
        left = int(left[1:])
        left_dec = 1

    # additions
    right = loc_changes[loc_changes.find(' ')+1:]
    right_dec = 0
    if right.find(',') > 0:
        comma = right.find(',')
        right_dec = int(right[comma+1:])
        right = int(right[1:comma])
    else:
        right = int(right[1:])
        right_dec = 1

    if left == right:
        return {left: (right_dec - left_dec)}
    else:
        return {left : left_dec, right: right_dec}



def is_loc_change(result, loc_changes):
    # search for loc changes (@@ ) and update loc_changes variable
    if result.startswith('@@'):
        loc_change = result[result.find(' ')+1:]
        loc_change = loc_change[:loc_change.find(' @@')]
        return loc_change
    else:
        return loc_changes

def is_new_file(result, file):
    # search for destination file (+++ ) and update file variable
    if result.startswith('+++'):
        return result[result.rfind(' ')+1:]
    else:
        return file

def get_commits(before, after, author, dir):
    # note --no-merges flag (usually we coders do not overhaul contributions)
    # note --reverse flag to traverse history from past to present
    command = 'git log --author="'+author+'" --format="%h" --no-abbrev '
    command += '--before="'+before+'" --after="'+after+'" --no-merges --reverse'

    # print(command)

    return get_proc_out(command, dir).splitlines()

# not used but still could be of value in the future
def get_files(commit, dir):
    # this also works in case --no-merges flag is ommitted prior
    command = 'git show --numstat --pretty="" ' + commit
    results = get_proc_out(command, dir).splitlines()
    for i in range(len(results)):
        # remove the tabbed stats from --numstat
        results[i] = results[i][results[i].rfind('\t')+1:]
    return(results)

def get_proc_out(command, dir):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=dir,
        shell=True
    )
    return process.communicate()[0].decode("utf-8")

if __name__ == '__main__':
    main()
