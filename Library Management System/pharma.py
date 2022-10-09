from cProfile import label
from msilib import Table
from sqlite3 import Row
from tkinter import*
from tkinter import ttk
from tkinter.tix import COLUMN
from tkinter.ttk import LabeledScale
from turtle import width
class libraryManagementSystem:
    def __init__(self,root):
        self.root=root
        self.root.title("library Management System")
        self.root.geometry("1550x800+0+0")

        lbltitle=Label(self.root,text="LIBRARY MANAGEMENT SYSTEM",bd=20,relief=RIDGE,bg='lightgray',fg="blue",font=("times new roman",50,"bold"),padx=2,pady=6)
                            
        lbltitle.pack(side=TOP,fill=X)
        frame=Frame(self.root,bd=12,relief=RIDGE,padx=20,bg="powder blue")
        frame.place(x=0,y=130,width=1530,height=400)

        # =======================DataFrameLeft==============

        DataFrameLeft=LabelFrame(frame,text="Library membership Information",bg="powder blue",fg="green",bd=12,relief=RIDGE,font=("times new roman",15,"bold"))
        DataFrameLeft.place(x=0,y=5,width=860,height=350)

        lblMemebr=Label(DataFrameLeft,text="Member type",bg="powder blue",font=("times new roman",15,"bold"),padx=2,pady=6)
        lblMemebr.grid(row=0,column=0,sticky=W)

        comMember=ttk.Combobox(DataFrameLeft,font=("times new roman",15,"bold"),width=27,state="readonly")
        comMember["value"]=("Admin Staf","Student","Lecturer")
        comMember.current(0)
        comMember.grid(row=0,column=1)

        lblPRN_NO=Label(DataFrameLeft,text="PRN NO",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblPRN_NO.grid(row=1,column=0,sticky=W)
        txtPRN_NO=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtPRN_NO.grid(row=1,column=1)

        lblTitle=Label(DataFrameLeft,text="ID no",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblTitle.grid(row=2,column=0,sticky=W)
        txtTitle=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtTitle.grid(row=2,column=1)

        lblFirstName=Label(DataFrameLeft,text="First  Name",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblFirstName.grid(row=3,column=0,sticky=W)
        txtFirstName=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtFirstName.grid(row=3,column=1)

        lblLastName=Label(DataFrameLeft,text="Last  Name",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblLastName.grid(row=4,column=0,sticky=W)
        txtLastName=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtLastName.grid(row=4,column=1)

        lblAddress1=Label(DataFrameLeft,text="Address 1",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblAddress1.grid(row=5,column=0,sticky=W)
        txtAddress1=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtAddress1.grid(row=5,column=1)

        lblAddress2=Label(DataFrameLeft,text="Address 2",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblAddress2.grid(row=6,column=0,sticky=W)
        txtAddress2=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtAddress2.grid(row=6,column=1)

        lblPostcode=Label(DataFrameLeft,text="Post code",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblPostcode.grid(row=7,column=0,sticky=W)
        txtPostcode=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtPostcode.grid(row=7,column=1)
 
        lblMobile=Label(DataFrameLeft,text="Mobile",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblMobile.grid(row=8,column=0,sticky=W)
        txtMobile=Entry(DataFrameLeft,font=("arial",13,"bold"),width=29)
        txtMobile.grid(row=8,column=1)

        lblBook_Id=Label(DataFrameLeft,text="Book Id",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblBook_Id.grid(row=0,column=2,sticky=W)
        txtBook_Id=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtBook_Id.grid(row=0,column=3)

        lblBook_Title=Label(DataFrameLeft,text="Book Title",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblBook_Title.grid(row=1,column=2,sticky=W)
        txtBook_Title=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtBook_Title.grid(row=1,column=3)

        lblAuthor_Name=Label(DataFrameLeft,text="Author Name",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblAuthor_Name.grid(row=2,column=2,sticky=W)
        txtAuthor_Name=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtAuthor_Name.grid(row=2,column=3)

        lblDataBorrowed=Label(DataFrameLeft,text="Data Borrowed",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblDataBorrowed.grid(row=3,column=2,sticky=W)
        txtDataBorrowed=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtDataBorrowed.grid(row=3,column=3)

        lblDataDue=Label(DataFrameLeft,text="Data Due",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblDataDue.grid(row=4,column=2,sticky=W)
        txtDataDuelbl=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtDataDuelbl.grid(row=4,column=3)

        lblDaysOnBook=Label(DataFrameLeft,text="Days On Book",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblDaysOnBook.grid(row=5,column=2,sticky=W)
        txtDaysOnBook=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtDaysOnBook.grid(row=5,column=3)

        lblLateReturnFine=Label(DataFrameLeft,text="Late Return Fine",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblLateReturnFine.grid(row=6,column=2,sticky=W)
        txtLateReturnFine=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtLateReturnFine.grid(row=6,column=3)

        lblDateOverDue=Label(DataFrameLeft,text="Date Over Due",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblDateOverDue.grid(row=7,column=2,sticky=W)
        txtDateOverDue=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtDateOverDue.grid(row=7,column=3)

        lblActualPrice=Label(DataFrameLeft,text="Actual Price",bg="powder blue",font=("arial",12,"bold"),padx=2,pady=6)
        lblActualPrice.grid(row=8,column=2,sticky=W)
        txtActualPrice=Entry(DataFrameLeft,font=("arial",12,"bold"),width=29)
        txtActualPrice.grid(row=8,column=3)

        #  =========================DataFrameRight=================================

        DataFrameRight=LabelFrame(frame,text="Book Details",bg="powder blue",fg="green",bd=12,padx=20,relief=RIDGE,font=("Arial",12,"bold"))
        DataFrameRight.place(x=870,y=5,width=580,height=350)

        self.txtBox=Text(DataFrameRight,font=("Arial",12,"bold"),width=32,height=16,padx=2,pady=6)
        self.txtBox.grid(row=0,column=2)

        listScrollBar=Scrollbar(DataFrameRight)
        listScrollBar.grid(row=0,column=1,sticky="ns")

        listBooks=['Python Programming',"Python codebook","Machine tecno","Advance Python","Inton Python","Elite Jungle Python","Machine Python","Jungle python","My python","Html","Css","JAVa","Javascript","React Java","PHP","SQL","DATABASE"]

        listBox=Listbox(DataFrameRight,font=("Arial",12,"bold"),width=20,height=16)
        listBox.grid(row=0,column=0,padx=4)
        listScrollBar.config(command=listBox.yview)

        for item in listBooks:
            listBox.insert(END,item)
        # =================Button=============

        Framebutton=Frame(self.root,bd=12,relief=RIDGE,padx=20,bg="powder blue")
        Framebutton.place(x=0,y=530,width=1530,height=70)

        btnAddData=Button(Framebutton,text="Add Data",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnAddData.grid(row=0,column=0)

        btnShowData=Button(Framebutton,text="Show Data",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnShowData.grid(row=0,column=1)

        btnDelete=Button(Framebutton,text="Delete",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnDelete.grid(row=0,column=2)

        btnUpdate=Button(Framebutton,text="Update",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnUpdate.grid(row=0,column=3)

        btnReset=Button(Framebutton,text="Reset",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnReset.grid(row=0,column=4)

        btnExit=Button(Framebutton,text="Exit",font=("Arial",12,"bold"),width=23,bg="red",fg="white")
        btnExit.grid(row=0,column=5)

        # ===================Details==============
        FrameDetails=Frame(self.root,bd=12,relief=RIDGE,padx=20,bg="powder blue")
        FrameDetails.place(x=0,y=590,width=1530,height=210)

        Table_frame=Frame(FrameDetails,bd=6,relief=RIDGE,bg="powder blue")
        Table_frame.place(x=0,y=2,width=1460,height=190)

        # self.library_table=ttk.Treeview(Table_frame,column=("membertype","prnno","Title","firstname","lastname","adress1","adress 2","mobile","bookkid","Author","datedue","days","laterreturnfine","dateoverdue"))
        # self.library_table.heading("membertype",text="Member Type")
        # self.library_table.heading("prnno",text="reference no")
        # self.library_table.heading("Title",text="Title")
        # self.library_table.heading("firstname",text="First Name")
        # self.library_table.heading("lastname",text="Last Name")
        # self.library_table.heading("adress1",text="adress 1")
        # self.library_table.heading("postkit",text="Post Id")
        
        # self.library_table.heading("adress2",text="adress 2")
        # self.library_table.heading("mobile",text="Mobile")
        # self.library_table.heading("bookkid",text="Book ID")
        # self.library_table.heading("author",text="Author")
        # self.library_table.heading("datedue",text="Member Type")
        # self.library_table.heading("days",text="Member Type")
        # self.library_table.heading("laterreturnfine",text="Member Type")
        # self.library_table.heading("dateoverdue",text="Member Type")
if __name__=="__main__":
    root=Tk()
    obj= libraryManagementSystem(root)
    root.mainloop() 
                           