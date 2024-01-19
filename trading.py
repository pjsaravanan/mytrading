# -*- coding: utf-8 -*-

import streamlit as st, pandas as pd, numpy as np
import pymongo
from breeze_connect import BreezeConnect
from bson.objectid import ObjectId
from datetime import datetime
import http.client
import hashlib
import json
from st_aggrid import AgGrid
from st_aggrid import grid_options_builder as gob
from time import sleep

mdbcon = "mongodb+srv://pjsaravanan:Saran%402810@mdbcluster.dhqbs.mongodb.net/mytrading?retryWrites=true&w=majority"
client = pymongo.MongoClient(mdbcon)
trdb = client.mytrading


app_key = "30G=e80786~232r727OtI4387xM#0194"
secret_key = "5Z45672$75D_6632*654231560443Ef3"
temptoken = trdb.apitoken.find_one({'_id' : ObjectId('63714ac05274e29cd3527086')}) 
mytoken = temptoken["stoken"]
strmytoken = str(mytoken)

breeze = BreezeConnect(app_key)
breeze.generate_session(api_secret=secret_key, session_token=mytoken)


existingpositions=pd.DataFrame({})
placedorders=pd.DataFrame({})
instruments= pd.DataFrame({})
mapper = {}

breeze.ws_connect()

# Callback to receive ticks.
def on_ticks(ticks):
    print("Ticks: {}".format(ticks))

# Assign the callbacks.
breeze.on_ticks = on_ticks
    
def ordernow():
    if amc == amcoptions[0]:
        orderresponse  = breeze.place_order(stock_code=mapper["selectedsymbol"],
                                            exchange_code=mapper["exchange_code"],
                                            product=mapper["product_type"].lower(),
                                            action=mapper["action"].lower(),
                                            order_type=mapper["ordertype"].lower(),
                                            stoploss=mapper["triggerprice"],
                                            quantity=mapper["qty"],
                                            price=mapper["limitprice"],
                                            validity="day",
                                            validity_date=datetime.now(),
                                            disclosed_quantity="0",
                                            expiry_date=mapper["m_expirydate"],
                                            right=mapper["rights"],
                                            strike_price=mapper["m_strike"])
        st.write(orderresponse)
        mapper["orderid"] = orderresponse["Success"]["order_id"]
        if amcplacetype==validordertypes[3]:
            mapper["action"]=mapper["targetaction"]
            mapper["qty"] = mapper["targetqty"]
            mapper["price"] = mapper["targetprice"]
            sleep(2)
            mapper["targetorderready"] = False
            while not mapper["targetorderready"]:
                print(f"checking status of INVADE orders {datetime.now()}")
                mapper["targetorderready"]=breeze.get_order_detail(exchange_code=mapper["exchange_code"], order_id=mapper["orderid"])["Success"][0]["status"]=="Executed" 
                sleep(2)
            if mapper["targetorderready"] :       
                squareoffnow()
def squareoffnow():

    breeze.square_off(stock_code=mapper["selectedsymbol"],
                                        exchange_code=mapper["exchange_code"],
                                        product=mapper["product_type"].lower(),
                                        action=mapper["action"].lower(),
                                        order_type=mapper["ordertype"].lower(),
                                        stoploss=mapper["triggerprice"],
                                        quantity=mapper["qty"],
                                        price=mapper["limitprice"],
                                        validity="day",
                                        validity_date=datetime.now(),
                                        disclosed_quantity="0",
                                        expiry_date=mapper["m_expirydate"],
                                        right=mapper["rights"],
                                        strike_price=mapper["m_strike"])
    
st.set_page_config(layout="wide")


insc1, insc2 = st.columns(spec=2, gap="small")

with insc1:
    r1 = st.container()
    with r1:
        st.header(":blue[Select Instrument]")
        c1, c2, c3, c4, c5, c6 = st.columns(spec=6, gap="small")
        
        with c1:
            basetype =["INDEX","STOCK"]
            mapper["symboltype"] = st.selectbox("Base Type",options=basetype)
            allsymbol = pd.DataFrame(list(trdb.symbolmapping.find({"IndexOrStock" : mapper["symboltype"]})))
            print(allsymbol)
            symbol = list(set(list(allsymbol["stock_code"])))
            symbol.sort()
        
        with c2:
            mapper["selectedsymbol"] = st.selectbox("Symbol",options=symbol)
            allsymbol = allsymbol[(allsymbol["stock_code"]==mapper["selectedsymbol"])]
            mapper["maxqty"] = allsymbol.iloc[0]["maxqty"]

        with c3:
            instrumenttype = ["FUTURE", "OPTION"]
            mapper["selectedinstrumenttype"] = st.selectbox("InstrumentType",options=instrumenttype)
            instrumentname = "FUT" if mapper["selectedinstrumenttype"]==instrumenttype[0] else "OPT" 
            mapper["instrumentname"] = instrumentname + ( "IDX" if mapper["symboltype"]== basetype[0] else "STK" )
            print(mapper["instrumentname"])
        
        with c4:
            m_instrument = pd.DataFrame(list(trdb.fnobasicdata.find({"ShortName"  : mapper["selectedsymbol"]})))
            m_instrument = m_instrument[(m_instrument["Series"]==mapper["selectedinstrumenttype"])]
            m_allexpirydate = list(set(list(m_instrument["ExpiryDate"])))
            m_allexpirydate.sort()
            m_allexpirydate = [date.strftime("%d-%b-%Y") for date in m_allexpirydate]
            print(m_allexpirydate )
            mapper["m_expirydate"] = st.selectbox("Expiry Date", options=m_allexpirydate)
            m_instrument = m_instrument[( m_instrument["ExpiryDate"]==mapper["m_expirydate"]) ]
            print(m_instrument)
        
        with c5:
            if instrumentname[0:3] == "OPT" :
                rights = ["CE", "PE"]
                mapper["m_rightchoice"] = st.selectbox("Rights", options=rights)
            else:
                mapper["m_rightchoice"] = "XX"
            m_instrument = m_instrument[ (m_instrument["OptionType"]==mapper["m_rightchoice"] )]
            if mapper["m_rightchoice"] == "XX":
                    mapper["rights"]= "others"
            elif mapper["m_rightchoice"] == "CE":
                    mapper["rights"]= "call"
            elif mapper["m_rightchoice"] == "PE":
                    mapper["rights"]= "put"
        
        with c6:
            if instrumentname[0:3] == "OPT" :
                m_allstrike = list(m_instrument["StrikePrice"])
                mapper["m_strike"]= st.selectbox("Strike Price", options=m_allstrike)
            else:
                mapper["m_strike"] = 0.0
            m_instrument = m_instrument[( m_instrument["StrikePrice"]==mapper["m_strike"] ) ]
            mapper["lotsize"] = m_instrument.iloc[0]["LotSize"]
            mapper["stktoken"] = m_instrument.iloc[0]["Token"]
            mapper["daystoexpire"] = m_instrument.iloc[0]["DaysToExpire"]
        rr1 = st.container()
        with rr1:
            c1, c2, c3, c4, c5, c6 = st.columns(spec=6, gap="small")

        # from_date = st.date_input("From Date",format="DD-MM-YYYY", on_change=changed).strftime("%d-%b-%Y")
        # to_date = st.date_input("To Date",format="DD-MM-YYYY", on_change=changed ).strftime("%d-%b-%Y")

            mapper["exchange_code"] = "NFO"         
            mapper["product_type"] = "futures" if instrumentname[0:3]=="FUT" else "options"
            mapper["curprice"] = breeze.get_quotes(stock_code=mapper["selectedsymbol"],
                    exchange_code=mapper["exchange_code"],
                    expiry_date=mapper["m_expirydate"],
                    product_type=mapper["product_type"],
                    right=mapper["rights"],
                    strike_price=mapper["m_strike"])["Success"][0]["ltp"]
            with c1:
                st.write(f"LTP      : :orange[{mapper['curprice']}] ")
            with c2:
                st.write(f"Max Qty  : :orange[{mapper['maxqty']}]")
            with c3:
                st.write(f"Lot Size : :orange[{mapper['lotsize']}]")
            with c4:
                st.write(f"Expires in : :orange[{mapper['daystoexpire']}]s")
            
#            breeze.subscribe_feeds(exchange_code="NFO", stock_code=selectedsymbol, product_type="options", expiry_date=m_expirydate, strike_price=str(m_strike), right=tempr, get_exchange_quotes=True, get_market_depth=False)
            
            # positions = ["New Positions", "Existing Positions"]
            # positionschoice = st.selectbox(label="Based on", options=positions)
    st.header(":blue[Manage Orders]")
    amcc1, amcc2, amcc3, amcc4, amcc5, amcc6, amcc7 = st.columns(7)
    with amcc1:
        amcoptions = ["Place", "Modify", "Cancel"]
        amc = st.radio("Orders", options=amcoptions, horizontal=False)
    with amcc2:
        if amc == amcoptions[0]:
            validordertypes = ["Market", "Limit", "StopLoss", "INVADE"]
            amcplacetype = st.radio("Order Type",options=validordertypes, horizontal=False)
            mapper["ordertype"] = "limit" if amcplacetype==validordertypes[3] else amcplacetype
            mapper["targetordertype"] = "limit"
    with amcc3:
        if amc == amcoptions[0]:        
            validactions = ["Buy", "Sell"]
            action = st.radio("Action", options=validactions)    
            mapper["action"] = action
            mapper["targetaction"] = "sell" if action==validactions[0] else "buy"
    with amcc4:
        if amc == amcoptions[0]:
            if amcplacetype == validordertypes[0]:
                mapper["limitprice"] = 0
            else:
#            if amcplacetype == validordertypes[1] or amcplacetype == validordertypes[2] :
                mapper["limitprice"] = st.number_input("Limit Price")
        
            if amcplacetype == validordertypes[2] :
                mapper["triggerprice"] = st.number_input("Trigger Price")
                
            if amcplacetype == validordertypes[3] :
                mapper["targetprice"] = st.number_input("Target Price")
                
                # qtysplitoptions = ["Equal", "Martingale", "Reverse Martingale"]
                # qtysplit = st.selectbox("Qty Split By", options = qtysplitoptions )
            
    with amcc5:
        if amc == amcoptions[0]  :
            mapper["qty"]= st.number_input("Lots",min_value=1, max_value=int(mapper["maxqty"]/mapper["lotsize"]))*mapper["lotsize"]
            st.write(f"Qty : :orange[{mapper['qty']}]")
            if amcplacetype == validordertypes[3] :
                mapper["targetqty"] = st.number_input("Target Lots",min_value=1, max_value=int(mapper["qty"]/mapper["lotsize"]))*mapper["lotsize"]
                st.write(f"Target Qty : :orange[{mapper['targetqty']}]")
            
    with amcc7:
        st.write("   ")
        st.write("   ")
        st.button("Place Order", on_click=ordernow, type="primary")

    if amc == "Modify":
        pass

    if amc == "Cancel":
        pass
    
    r2 = st.container()
    with r2:
        st.header(":blue[----------------------------------------]")
        # poc1, poc2, poc3, poc4, poc5, poc6, poc7 = st.columns(7)
        # with poc1:
        #     validactions = ["Buy", "Sell"]
        #     action = st.selectbox("Action", options=validactions)
    
        # with poc2:
            
        #     ordertype = st.selectbox("Order Type", options=validordertypes )
            
        # with poc3:
        #     if ordertype != validordertypes[1]:
        #         limitprice = st.number_input("Limit Price")
                
        # with poc4:
        #     if ordertype == validordertypes[2]:
        #         triggerprice = st.number_input("Trigger Price")
                
        # with poc7:
        #     st.write(" ")
        #     st.write(" ")        
        #     st.button("Place Order", on_click=ordernow, type="primary")


       
#builds a gridOptions dictionary using a GridOptionsBuilder instance.
def buildgridoptions(df):
    builder = gob.GridOptionsBuilder.from_dataframe(df)
    builder.configure_pagination(paginationPageSize=100)
    builder.configure_column(
        field="ShortName",
        rowGroup=True,  )
    go = builder.build()
    return go


with insc2:
    r1 = st.container()
    with r1:
       st.header(":blue[Existing Positions]",)
       existingpositions = pd.DataFrame(breeze.get_portfolio_positions()["Success"]) 
       AgGrid(existingpositions, fit_columns_on_grid_load=False, columns_auto_size_mode=2)

    r2 = st.container()
    with r2:
       st.header(":blue[Pending Orders]")
       sc1, sc2 = st.columns(spec=2, gap="large")
       with sc1:
           from_date = st.date_input("From Date",format="DD-MM-YYYY").strftime("%d-%b-%Y")
       with sc2:
           to_date = st.date_input("To Date",format="DD-MM-YYYY").strftime("%d-%b-%Y")
       placedorders = pd.DataFrame(breeze.get_order_list(exchange_code="NFO", from_date = from_date, to_date=to_date)["Success"])    
       print(placedorders)
       if placedorders.shape[0] > 0:
           placedorders = placedorders[( placedorders["status"]!= "Cancelled") & (placedorders["status"] != "Expired" ) & (placedorders["status"] !=  "Executed")]
           AgGrid(placedorders,  fit_columns_on_grid_load=False, columns_auto_size_mode=2)
       else:
           st.write(" ")
           st.write(" ")
           st.markdown(":orange[**No pending on matching criteria**]")
