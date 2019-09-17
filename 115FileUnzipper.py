import os
import shutil
import zipfile
import datetime
import socket
import platform
import time

SCRIPT_VERSION = "v1.0"

#################################################################################################
#                                                                                               #
#   name:   Sean Lissner                                                                        #
#   email:  slissner@usc.edu                                                                    #
#                                                                                               #
#   How To:                                                                                     #
#   1. Create a new folder to contain all of the files for the assignment you want to grade     #
#   2. Put this script and zip file downloaded from BB into this folder                         #
#   3. Set the configuration details by setting ACCEPTED_FORMATS and DELIVERABLE_TYPE vars      #
#   4. Run the script                                                                           #
#   5. All the .py files should now be under "ReadyToGrade" in each student's corresponding     #
#      personal folder (Assignment configuration).                                              #
#                                                                                               #
#   NOTES:                                                                                      #
#       - The program checks to see if the zip is corrupted or if it doesn't want to open       #
#         it prints all the corrupted files in the command line before it terminates            #
#                                                                                               #
#################################################################################################


# -------------- MODIFY THE FOLLOWING AS NECESSARY -------------- #

# Add any file extensions you want the program to extract from the student's zip file
ACCEPTED_FORMATS = [".py", ".txt", ".csv", ".dat"]

# Names of folders that we want the script to ignore (hidden folders, config info, etc.)
IGNORE_FOLDERS = ["venv", "bin", ".idea", "lib", "include"]

# "A" is for assignment config and "L" is for lab config
#   - Assignment configuration creates sub directories for each student to to make file organisation easier
#   - Lab configuration just puts all of the .py files into ReadyToGrade
DELIVERABLE_TYPE = "A"

# --------------------------------------------------------------- #


def main():

    info = {}                        # For runtime information
    t0 = time.perf_counter()
    studentCount = 0

    if checkConfig() == False:       # Checks that configs are correct
        return

    corruptedFiles = []              # Stores the names of any corrupted files
    successfulFiles = []             # Stores the names of the successfully unzipped files
    moveErrors = []                  # Stores any caught file moving errors

    cwd = os.getcwd()                # Gets the file path to current working dir

    newDirs = [cwd + "/ReadyToGrade/",
               cwd + "/AllLeftoverFiles/",
               cwd + "/AllLeftoverFiles/" + "StudentFiles/",
               cwd + "/AllLeftoverFiles/" + "StudentZips/"]

    # List of files in current dir
    source = os.listdir(cwd)

    numZips = 0
    for file in source:
        if file.endswith(".zip"):
            numZips += 1

    if numZips > 1:
        print("Too many .zip files in the working directory. Exiting.")
        return
    if numZips == 0:
        print("Could not find any .zip files in the working directory. Exiting.")
        return

    if mkdir(newDirs) == False:     # Creates the dirs we will be reading into
        return                      # Exits program if directories have already been built

    readyToGradeDir = newDirs[0]                # dir/ReadyToGrade/
    allLeftoverFilesDir = newDirs[1]            # dir/AllLeftoverFiles/     (currently unused var)
    leftoverStudentFilesDir = newDirs[2]        # dir/AllLeftoverFiles/StudentFiles
    leftoverStudentZipsDir = newDirs[3]         # dir/AllLeftoverFiles/StudentZips

    for file in source:               # Unzipping main file from blackboard
        if file.endswith(".zip"):
            zip_ref = zipfile.ZipFile(file, 'r')
            zip_ref.extractall(leftoverStudentZipsDir)
            zip_ref.close()

    # List of zip files + txt files from unzipping master
    unzippedSource = os.listdir(leftoverStudentZipsDir)

    for file in unzippedSource:     # Unzipping all the individual student zip files
        if file.endswith(".zip"):
            try:
                studentCount += 1
                # Unzip file into LeftoverStudentFiles
                zip_ref = zipfile.ZipFile(leftoverStudentZipsDir + file, 'r')
                zip_ref.extractall(leftoverStudentFilesDir)
                zip_ref.close()

                fileDest = readyToGradeDir              # Default case if DELIVERABLE_TYPE == "L"

                if DELIVERABLE_TYPE.upper() == "A":     # File destination depends on configuration

                    userName = getUsername(file)        # Get username from filename
                    fileDest = readyToGradeDir+userName

                    if not os.path.exists(fileDest):    # Creating personal dir to unzip file into
                        os.makedirs(fileDest)

                # Searches for non-invisible .py files recursively
                recursiveFileMover(leftoverStudentFilesDir, fileDest, moveErrors)

                # Saves name of file into list for printing to logfile
                successfulFiles.append(file)

            except zipfile.BadZipFile:
                # Saves name of file for printing to logfile
                corruptedFiles.append(file)

    t1 = time.perf_counter()
    info["time"] = str(round(t1-t0, 4))
    info["count"] = studentCount

    generateLogFile(corruptedFiles, successfulFiles, moveErrors, info)    # Writes all data to logfile


# Inputs:   Path             - The current directory where this function is looking for py files
#           readytoGradePath - path to the folder where all the py files need to be moved to
# Notes:    This function is called recursively in case there is a folder hierarchy hiding the
#           student's py file.
def recursiveFileMover(path, readyToGradePath, moveErrors):
    source = os.listdir(path)

    for file in source:
        # checks that the extension is accepted and it's not an invisible file
        if (os.path.splitext(file)[1].lower() in ACCEPTED_FORMATS) \
                and not file.startswith("."):
                # and file != "__init__.py":
            try:
                shutil.move(path+"/"+file, readyToGradePath)        # move it to the right directory
            except shutil.Error:
                moveErrors.append("Error moving file: \n\t" + path + file
                                  + "\nTo location: \n\t" + readyToGradePath + "\n\n")

        elif os.path.isdir(path+"/"+file) and file not in IGNORE_FOLDERS:
            print(file)
            recursiveFileMover(path+"/"+file, readyToGradePath, moveErrors)


# Inputs:   corruptedFiles  - List containing the zip files that were corrupted
#           successfulFiles - List containing the zip files that were unzipped successful
# Notes:    Generates a log file with info about when the script was run, system, corrupted/non-corrupted zips
def generateLogFile(corruptedFiles, successfulFiles, moveErrors, info):

    currentDT = datetime.datetime.now()  # Gets current time

    outfile = open("logfile_" + currentDT.strftime("%Y-%m-%d_%H-%M-%S") +".txt", "w")

    outfile.write("SYSTEM INFORMATION:\n")
    outfile.write("Timestamp:\t\t\t\t" + currentDT.strftime("%Y-%m-%d %H:%M:%S") + "\n")     # prints timestamp
    outfile.write("System:\t\t\t\t\t" + socket.gethostname() + "\n")                         # prints hostname
    outfile.write("Platform:\t\t\t\t" + platform.platform() + "\n")                          # prints platform
    outfile.write("Version:\t\t\t\t" + SCRIPT_VERSION)                                       # prints the version
    outfile.write("\n\nCONFIG INFORMATION:")
    outfile.write("\nDeliverable Type:\t\t" + DELIVERABLE_TYPE)
    outfile.write("\nAccepted Formats:\t\t" + str(ACCEPTED_FORMATS))

    outfile.write("\n\nRUNTIME INFORMATION:")
    outfile.write("\nScript execution time:\t" + info["time"])
    outfile.write("\nTotal students:\t\t\t" + str(info["count"]))

    # If corruptedFiles NOT empty, prints all corrupted files
    if corruptedFiles:
        outfile.write("\n\n        **************************************************\n\n")
        outfile.write("The following .zip files (" + str(len(corruptedFiles)) + "/" + str(info["count"])
                      + ") were found to be corrupted: \n\n")
        for file in corruptedFiles:
            outfile.write("\t" + file + "\n")
    else:
        outfile.write("\n\n        **************************************************\n\n")
        outfile.write("No .zip files were found to be corrupted\n")

    # If moveErrors NOT empty, prints all move errors
    if moveErrors:
        outfile.write("\n\n        **************************************************\n\n")
        outfile.write("The following file moves couldn't be completed:\n\n")
        for move in moveErrors:
            outfile.write(move)
    else:
        outfile.write("\n\n        **************************************************\n\n")
        outfile.write("All files moved successfully \n")

    # Printing all successfully unzipped files
    outfile.write("\n\n        **************************************************\n\n")
    outfile.write("The following .zip files (" + str(len(successfulFiles)) + "/" + str(info["count"])
                  + ") were successfully unzipped: \n\n")
    for file in successfulFiles:
        outfile.write("\t" + file + "\n")


# Takes in the name of the zip file generated by blackboard and returns the userName from the filename
def getUsername(fileName):
    parts = fileName.split("_")
    return parts[1]


# Input: newDirs is a list containing the names of all the subdirectories to be created
# mkdir generates all the necessary subdirectories the script will use
def mkdir(newDirs) -> bool:

    for directory in newDirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            print("\n" + directory
                  + "\n Directory already exists. Move script and .zip to clean directory and try again")
            return False
    return True


# Checks the config settings, returns true if everything is correct, else false
def checkConfig() -> bool:

    # Checking deliverable type
    if (DELIVERABLE_TYPE.upper() != "A" and DELIVERABLE_TYPE.upper() != "L"):
        return False

    # Checking accepted formats
    for ext in ACCEPTED_FORMATS:
        if not (ext.startswith(".")):
            return False

    return True

main()