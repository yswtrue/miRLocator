# -*- coding: utf-8 -*-
import os, sys
import source
import zipfile
#end

##################################################################################################
##############################parameters section##################################################
##################################################################################################
##the directory of RNAfold                                                                     ###
RNAFoldDic = "/usr/bin/"  ###
###
##file directory of source.py                                                                  ###
# sourceDic = "/home/cma/Researches/matureMiRNA/miRLocator/"  ###
sourceDic = os.path.join(os.getcwd()) + '/'  ###
###
##result directory, include trainDataFileName, predDataFileName, predDataAnnotFileName         ###
resultDic = sourceDic + "static/results/"  ###
###
###
##a logical parameter indicate whether run cross validation on training dataset
cross_validation_flag = False  ###
###
##miRNAs and pre-miRNAs for training                                                           ###
trainDataFileName = "trainingData.txt"  ###
##pre-miRNAs for prediction                                                                    ###
predDataFileName = "predictionData.txt"  ###
##the annotated miRNAs and pre-miRNAs for prediction dataset                                   ###
###
###
##################################optional parameters ############################################
##the full path of trained prediction model. If a full path is given,                          ###
##miRLocator will locate it directly, otherwise, miRLocator will run the training program.     ###
predModelFileDir = ""  ###
##If the file name is defined, miRLocator will evaluate the prediction results                 ###
##based on annotation infomation in this file                                                  ###
predDataAnnotFileName = "predictionData_Annotated.txt"  ###


def start(training_data_path, prediction_data_path,
          prediction_data_annotated_path):
    """开始执行任务"""
    global RNAFoldDic
    global sourceDic
    global resultDic
    global cross_validation_flag
    global trainDataFileName
    global predDataFileName
    global predModelFileDir
    global predDataAnnotFileName
    global tempFileDir
    #keep this command, temp file used to record temporary results
    tempFileDir = resultDic + "tempResult.txt"

    predResultFileDir = resultDic + "miRLocator_predResults.txt"
    evalResultFileDir = resultDic + "miRLocator_evalResults.txt"

    #create file directories for recording dp_ss files for training and prediction
    dpSSFileDic_train = resultDic + "dp_ss_train/"
    dpSSFileDic_pred = resultDic + "dp_ss_pred/"

    source.createDict(dpSSFileDic_train)
    source.createDict(dpSSFileDic_pred)

    trainDataFileDir_Ref = source.checkFileForTraining(
        training_data_path,
        RNAFoldDic,
        sourceDic,
        dpSSFileDic_train,
        dpSSFlag=True)

    ##cross_validation_test
    if (cross_validation_flag == True):
        source.cross_validation_function(
            source.cv, trainDataFileDir_Ref, source.minCandidateMiRNALen,
            source.maxCandidateMiRNALen, source.upOffSet, source.downOffSet,
            source.minPredScore, resultDic, dpSSFileDic_train, RNAFoldDic,
            tempFileDir)
    #end if

    ##train prediction model on all miRNAs in input file
    ##trainDataFileDir_Ref: refined data for training
    ##dpSSFileDic_train: dp_ss files for training data
    ##RNAFoldDic: the directory of RNAfold
    ##tempFileDir: tempoary file
    ##source.upOffSet: 5 in default
    ##source.downOffSet: 5 in default
    #predModelFileDir: the full path of trained prediction model
    ##resultDic: result directory
    predModel = ""
    if (len(predModelFileDir) == 0):
        predModelFileDir = resultDic + "trained_prediction_model"
        predModel = source.train_prediction_model(
            trainDataFileDir_Ref, dpSSFileDic_train, RNAFoldDic, tempFileDir,
            source.upOffSet, source.downOffSet, predModelFileDir, resultDic)
    else:
        predModel = source.loadPredModel(predModelFileDir)
    #end else

    #prediction mature miRNAs within pre-miRNA sequences
    ##predDataFileDir_Ref:refined data for prediction
    ##dpSSFileDic_pred: dp_ss files for prediction
    ##RNAFoldDic:the directory of RNAfold
    ##tempFileDir:tempoary file
    ##source.minCandidateMiRNALen: 16 in default
    ##source.maxCandidateMiRNALen: 30 in default
    ##source.upOffSet: 5 in default
    ##source.downOffSet: 5 in default
    ##source.minPredScore: 0.25 in default, but not used in this version
    ##predModel: trained prediction model
    ##predResultFileDir: the full path of prediction results
    predDataFileDir_Ref = ""
    if (len(predDataFileName) > 0):
        predDataFileDir_Ref = source.checkFileForPrediction(
            prediction_data_path,
            RNAFoldDic,
            sourceDic,
            dpSSFileDic_pred,
            dpSSFlag=True)
        source.prediction(predDataFileDir_Ref, dpSSFileDic_pred, RNAFoldDic,
                          tempFileDir, source.minCandidateMiRNALen,
                          source.maxCandidateMiRNALen, source.upOffSet,
                          source.downOffSet, source.minPredScore, predModel,
                          predResultFileDir)

    #evaluate the prediction results
    ##predDataAnnotFileDir: the annotation of pre-miRNAs used for prediction. For each pre-miRNA, the annotation information include: miRNA_ID, pre-miRNA_ID, miRNA_seq, pre-miRNA_seq, pre-miRNA_structure
    ##predResultFileDir: the full path of predicted results output by miRLocator
    ##evalResultFileDir: the full path of evaluation result
    if (len(predDataAnnotFileName) > 0):
        source.eval_dif_resolutions(prediction_data_annotated_path,
                                    predResultFileDir, evalResultFileDir)


def zipdir(path, zip_path):
    zipFile = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
    # zip_path: is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            if os.path.join(root, file) != zip_path:
                zipFile.write(
                    os.path.join(root, file),
                    arcname=os.path.relpath(os.path.join(root, file), path))
    zipFile.close()
