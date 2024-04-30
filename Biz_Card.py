

import pandas as pd
import numpy as np
import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3 as sql
from pyngrok import ngrok
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re
import easyocr
import io


#Getting Image input
def Image_into_Text(locat):
  Image_Inpt=Image.open(locat)

  #Converting Image to Array
  Image_Array=np.array(Image_Inpt)


  Read=easyocr.Reader(['en'])

  Text=Read.readtext(Image_Array,detail=0)
  return Text, Image_Inpt


def extracted_text(texts):
  extrd_dict = {"NAME" : [], "DESIGNATION":[], "COMPANY_NAME": [], "CONTACT": [], "EMAIL":[], "WEBSITE":[],
                "ADDRESS":[], "PINCODE":[]}

  extrd_dict["NAME"].append(texts[0])
  extrd_dict["DESIGNATION"].append(texts[1])

  for i in range(2,len(texts)):

    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):

      extrd_dict["CONTACT"].append(texts[i])

    elif "@" in texts[i] and ".com" in texts[i]:
       extrd_dict["EMAIL"].append(texts[i])

    elif "WWW" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i] or "www" in texts[i]:
       small= texts[i].lower()
       extrd_dict["WEBSITE"].append(small)

    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extrd_dict["PINCODE"].append(texts[i])

    elif re.match(r'^[A-Za-z]', texts[i]):
      extrd_dict["COMPANY_NAME"].append(texts[i])

    else:
      remove_colon = re.sub(r'[,;]' ,'' ,texts[i])
      extrd_dict["ADDRESS"].append(remove_colon)

  for key,value in extrd_dict.items():
    if len(value)>0:
      concadenate=" ".join(value)
      extrd_dict[key] = [concadenate]

    else:
      value ="NA"
      extrd_dict[key] = [value]

  return extrd_dict


# STREAMLIT AREA -- CODE HERE

st.set_page_config(layout="wide")

st.header(':rainbow[BizCardX: Extracting Business Card Data with OCR]', divider='rainbow')

select=option_menu(None, ["Home", "Upload"], orientation="horizontal")

if select=="Home":
  st.header(":orange[BizCardX: Extracting Business Card Data with OCR]")
  st.subheader(":blue[Technologies] : :gray[OCR,streamlit GUI, SQL,Data Extraction]")

if select=="Upload":

  tab1, tab2, tab3 = st.tabs(["UPLOAD IMAGE & EXTRCT TEXT", "MODIFY DATA", "DELETE DATA"])

  with tab1:
    img=st.file_uploader("UPLOAD IMAGE HERE", type=["png", "jpg", "jpeg"])

    if img is not None:
      st.subheader(":orange[HERE IS YOUR IMAGE]", divider='rainbow')
      st.image(img, width=400)

      tx_img,inp_img=Image_into_Text(img)

      tx_dic=extracted_text(tx_img)

      st.success("Text Extracted Successfully")

      #CONVERTING INTO DATAFRAME OF extracted_text
      DF = pd.DataFrame(extracted_text(tx_img))

      # CONVERTING IMAGE TO BYTES
      Img_Byt=io.BytesIO()
      inp_img.save(Img_Byt, format="PNG")

      Img_Data=Img_Byt.getvalue()

      #STORE BYTEES IN DICTONARY
      Byt_Data={"IMAGE" : [Img_Data]}
      DF_Byt=pd.DataFrame(Byt_Data)

      Concat_Img_DF = pd.concat([DF, DF_Byt], axis=1)

      st.dataframe(Concat_Img_DF)

      if st.button("SAVE"):

        # sql connection
        mydb = sql.connect("BizCardx")
        mycursor = mydb.cursor()

        #creating table
        mycursor.execute('''create table if not exists BizCard_Details(NAME varchar(100),
                                                                      DESIGNATION varchar(100),
                                                                      COMPANY_NAME varchar(100),
                                                                      CONTACT varchar(100),
                                                                      EMAIL varchar(100),
                                                                      WEBSITE text,
                                                                      ADDRESS text,
                                                                      PINCODE varchar(100),
                                                                      IMAGE text)''')
        mydb.commit()


        #INSERTING VALUE INTO THE COLUMN
        Insert_val_in_col=('''insert into BizCard_Details(NAME,
                                                        DESIGNATION ,
                                                        COMPANY_NAME,
                                                        CONTACT ,
                                                        EMAIL ,
                                                        WEBSITE,
                                                        ADDRESS,
                                                        PINCODE,
                                                        IMAGE)

                                                        values(?,?,?,?,?,?,?,?,?)''')

        datas= Concat_Img_DF.values.tolist()[0]
        mycursor.execute(Insert_val_in_col,datas)
        mydb.commit()
        st.success("Datas saved in Sql Successfully")

    mydb = sql.connect("BizCardx")
    mycursor = mydb.cursor()

    try:
      #SQL QUERY
      query1="select * from BizCard_Details"
      mycursor.execute(query1)
      dt=mycursor.fetchall()
      mydb.commit()

      df1=pd.DataFrame(dt, columns=[i[0] for i in mycursor.description])

      st.subheader(":orange[THIS IS SQL DATABASE]", divider='rainbow')
      st.dataframe(df1)

    except:
      pass


  with tab2:

    mydb = sql.connect("BizCardx")
    mycursor = mydb.cursor()

    try:
      #SQL QUERY
      query1="select * from BizCard_Details"
      mycursor.execute(query1)
      dt=mycursor.fetchall()
      mydb.commit()

      df2=pd.DataFrame(dt, columns=[i[0] for i in mycursor.description])

      st.subheader(":orange[THIS IS SQL DATABASE]", divider='rainbow')
      st.dataframe(df2)


      Name_Selected = st.selectbox(":orange[SELECT THE NAME TO MODIFY]", df2["NAME"].unique())

      df3=df2[df2["NAME"] == Name_Selected]

      st.subheader(":orange[THIS IS SELECTED NAME FROM SQL DATABASE]", divider='rainbow')
      st.dataframe(df3)

      df4=df3.copy()
    except:
      pass

    col1,col2,col3=st.columns(3)

    with col1:
      M_NA=st.text_input("NAME", *df3["NAME"].unique())
      M_DE=st.text_input("DESIGNATION", *df3["DESIGNATION"].unique())
      M_CN=st.text_input("COMPANY_NAME", *df3["COMPANY_NAME"].unique())

      df4["NAME"] = M_NA
      df4["DESIGNATION"] = M_DE
      df4["COMPANY_NAME"] = M_CN

    with col2:
      M_CT=st.text_input("CONTACT", *df3["CONTACT"].unique())
      M_EM=st.text_input("EMAIL", *df3["EMAIL"].unique())
      M_WS=st.text_input("WEBSITE", *df3["WEBSITE"].unique())

      df4["CONTACT"] = M_CT
      df4["EMAIL"] = M_EM
      df4["WEBSITE"] = M_WS


    with col3:
      M_ADD=st.text_input("ADDRESS", *df3["ADDRESS"].unique())
      M_PN=st.text_input("PINCODE", *df3["PINCODE"].unique())
      M_IM=st.text_input("IMAGE", *df3["IMAGE"].unique())


      df4["ADDRESS"] = M_ADD
      df4["PINCODE"] = M_PN
      df4["IMAGE"] = M_IM

    st.subheader(":orange[THIS IS MODIFIED DATA FROM SQL DATABASE]", divider='rainbow')
    st.dataframe(df4)

    col1,col2=st.columns(2)

    if st.button("Modify"):

      # sql connection
      mydb = sql.connect("BizCardx")
      mycursor = mydb.cursor()

      mycursor.execute(f"DELETE FROM BizCard_Details WHERE NAME = '{Name_Selected}'")
      mydb.commit()

      #creating table
      mycursor.execute('''create table if not exists BizCard_Details(NAME varchar(100),
                                                                    DESIGNATION varchar(100),
                                                                    COMPANY_NAME varchar(100),
                                                                    CONTACT varchar(100),
                                                                    EMAIL varchar(100),
                                                                    WEBSITE text,
                                                                    ADDRESS text,
                                                                    PINCODE varchar(100),
                                                                    IMAGE text)''')
      mydb.commit()


      #INSERTING VALUE INTO THE COLUMN
      Insert_val_in_col=('''insert into BizCard_Details(NAME,
                                                      DESIGNATION ,
                                                      COMPANY_NAME,
                                                      CONTACT ,
                                                      EMAIL ,
                                                      WEBSITE,
                                                      ADDRESS,
                                                      PINCODE,
                                                      IMAGE)

                                                      values(?,?,?,?,?,?,?,?,?)''')

      datas2= df4.values.tolist()[0]
      mycursor.execute(Insert_val_in_col,datas2)
      mydb.commit()

      st.success("Datas Modified in Sql Data Base Successfully")

      try:
        #SQL QUERY
        query2="select * from BizCard_Details"
        mycursor.execute(query2)
        dt2=mycursor.fetchall()
        mydb.commit()

        df5=pd.DataFrame(dt2, columns=[i[0] for i in mycursor.description])

        st.subheader(":orange[THIS IS FINAL SQL DATABASE AFTER MODIFICATION]", divider='rainbow')
        st.dataframe(df5)
      except:
        pass


  with tab3:
    # sql connection
    mydb = sql.connect("BizCardx")
    mycursor = mydb.cursor()

    col1,col2 = st.columns(2)
    with col1:

      try:
        #SQL QUERY
        query1="select NAME from BizCard_Details"
        mycursor.execute(query1)
        dt_2=mycursor.fetchall()
        mydb.commit()

        df_2=pd.DataFrame(dt_2, columns=[i[0] for i in mycursor.description])
      except:
        pass

      names=[]
      for i in df_2["NAME"]:
        names.append(i)

      name_select = st.selectbox("Select the name", names)

    with col2:
      query2 = f"SELECT DESIGNATION FROM BizCard_Details WHERE NAME ='{name_select}'"

      mycursor.execute(query2)
      dt_2=mycursor.fetchall()
      mydb.commit()

      df_2=pd.DataFrame(dt_2, columns=[i[0] for i in mycursor.description])

      destinat=[]
      for i in df_2["DESIGNATION"]:
        destinat.append(i)

      designation_select = st.selectbox("Select the designation", options = destinat)

    if name_select and designation_select:
      
      remove = st.button("Delete")
      if remove:

        mycursor.execute(f"DELETE FROM BizCard_Details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}'")
        mydb.commit()

        st.warning("DELETED")
      #SQL QUERY
      query3="select * from BizCard_Details"
      mycursor.execute(query3)
      dt3=mycursor.fetchall()
      mydb.commit()

      df6=pd.DataFrame(dt3, columns=[i[0] for i in mycursor.description])

      st.subheader(":orange[THIS IS FINAL SQL DATABASE AFTER DELETION]", divider='rainbow')
      st.dataframe(df6)


