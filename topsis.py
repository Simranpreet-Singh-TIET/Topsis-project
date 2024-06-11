import pandas as pd
import streamlit as st
import sys
import logging
import numpy as np
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_mail(email_id,resultfile):
    fromaddr = "simranmangat700@gmail.com"
    toaddr = email_id
   

# instance of MIMEMultipart
    msg = MIMEMultipart()
  
# storing the senders email address  
    msg['From'] = fromaddr
  
# storing the receivers email address 
    msg['To'] = toaddr
  
# storing the subject 
    msg['Subject'] = "TOPSIS SCORE AND RANK GENERATOR" 
  
# string to store the body of the mail
    body = '''For the given input file(.csv), here is your ouput(.csv) file with topsis score and rank information provided for MCDM(Multiple Criteria Decision Making)'''
  
# attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))
  
# open the file to be sent 
    filename = resultfile
    attachment = open(resultfile, "rb")
  
# instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')
  
# To change the payload into encoded form
    p.set_payload((attachment).read())
  
# encode into base64
    encoders.encode_base64(p)
   
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
  
# attach the instance 'p' to instance 'msg'
    msg.attach(p)
  
# creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
  
# start TLS for security
    s.starttls()
  
# Authentication
    s.login(fromaddr, "mjimbnrdjgmbcmxf") #Here password will be unique for every users...
  
# Converts the Multipart msg into a string
    text = msg.as_string()
  
# sending the mail
    s.sendmail(fromaddr, toaddr, text)
  
# terminating the session
    s.quit()

# Topsis Function:
# Checking the given input constraints

def topsis(db,weights,impacts,resultfile,email_id):
        
    if(db.shape[1]<3):
        print("Excel file must contain atleast 3 columns")
        sys.exit(1)
    
    
    weights=weights.split(',')
        
    impacts=impacts.split(',')

    
    if ((len(weights) == len(impacts)==(db.shape[1]-1))==False):
        print("Number of columns ,impacts and weights must be same.Try Again!")
        sys.exit(1)
        
    for imp in impacts :
        if(imp=='+' or imp=='-'):
            continue
        else:
            print("Impacts should only contain '+' or '-' symbols")
            sys.exit(1)
            
    cate_features=[i for i in db.columns[1:] if db.dtypes[i]=='object']
    if(len(cate_features)!=0):
        print("All columns except first should contain only numerical values! Try Again")
        sys.exit(1)

# Normalisation
    features = db.iloc[:,1:].values


    options = db.iloc[:,0].values    
    sumcols=[0]*len(features[0])


    for i in range(len(features)):
        for j in range(len(features[i])):
            sumcols[j]+=np.square(features[i][j])
            
    for i in range(len(sumcols)):
        sumcols[i]=np.sqrt(sumcols[i])
        

#Diving by root of sum of squares
    for i in range(len(features)):
        for j in range(len(features[i])):
            features[i][j]=features[i][j]/sumcols[j]
          
        
    weighted_feature_values=[]
    weights = np.array(weights, dtype=int)
    for i in range(len(features)):
        temp=[]
        for j in range(len(features[i])):
            temp.append(features[i][j]*(weights[j]))
        weighted_feature_values.append(temp)
        
    weighted_feature_values = np.array(weighted_feature_values)



# Calculating  ideal best and worst values..

    Ibest=[]
    Iworst=[]
    for i in range(len(weighted_feature_values[0])):
        Ibest.append(weighted_feature_values[0][i])
        Iworst.append(weighted_feature_values[0][i])

    
    for i in range(1,len(weighted_feature_values)):
        for j in range(len(weighted_feature_values[i])):
            if impacts[j]=='+':
                if weighted_feature_values[i][j]>Ibest[j]:
                   Ibest[j]=weighted_feature_values[i][j]
                elif weighted_feature_values[i][j]<Iworst[j]:
                    Iworst[j]=weighted_feature_values[i][j]
            elif impacts[j]=='-':
                if weighted_feature_values[i][j]<Ibest[j]:
                    Ibest[j]=weighted_feature_values[i][j]
                elif weighted_feature_values[i][j]>Iworst[j]:
                    Iworst[j]=weighted_feature_values[i][j]
                    
    Sjpositive=[0]*len(weighted_feature_values)
    Sjnegative=[0]*len(weighted_feature_values)
    for i in range(len(weighted_feature_values)):
        for j in range(len(weighted_feature_values[i])):
            Sjpositive[i]+=np.square(weighted_feature_values[i][j]-Ibest[j])
            Sjnegative[i]+=np.square(weighted_feature_values[i][j]-Iworst[j])



    for i in range(len(Sjpositive)):
        Sjpositive[i]=np.sqrt(Sjpositive[i])
        Sjnegative[i]=np.sqrt(Sjnegative[i])
        

    performance_score=[0]*len(weighted_feature_values)
    for i in range(len(weighted_feature_values)):
        performance_score[i]=Sjnegative[i]/(Sjnegative[i]+Sjpositive[i])

        
    final_scores_sorted = np.argsort(performance_score) # this returns indices of elements in sorted order
    max_index = len(final_scores_sorted)
    rank = []
    for i in range(len(final_scores_sorted)):
            rank.append(max_index - np.where(final_scores_sorted==i)[0][0])# since we know final_scores_sorted is already sorted, so it will need ranking from back side, so we need to subtract from maximum and get first value of tuple returned by np.where function
    rank_db = pd.DataFrame({"TOPSIS Score" : performance_score, "Ranks": np.array(rank)})


    db = pd.concat([db,rank_db],axis=1)
    db.to_csv(resultfile, index=False)
    send_mail(email_id,resultfile)
    st.success("Check your email, result file is successfully sent")



st.title("Topsis in seconds by Simran")

if __name__ == "__main__":
     file = st.file_uploader("Choose a file")
     w= st.text_input("Enter weight seperated by comma")
     i = st.text_input("Enter impact seperated by comma")
     m = st.text_input("Enter the email")
     submit_button=st.button("Send")
     if submit_button:
                    try:
                  
                        df = pd.read_csv(file)
                        topsis(df,w,i,"result_topsis.csv",m)
                    except Exception as e:
                        st.error(e)   
