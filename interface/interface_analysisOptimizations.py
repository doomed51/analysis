import sqlite3
import config
import datetime
import pandas as pd
import sys

from rich import print 


class AnalysisOptimizationsDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)

    def connect(self): ## redundant function as we connect on init 
        self.conn = sqlite3.connect(self.db_path)

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    """
        updates meta data of saved analyses. 
        inputs: 
            symbol
            analysis_name
    """
    def _update_analysis_metadata(self, symbol, analysis_name):
        tablename = 'updateHistory'
        currentdate = datetime.datetime.now()
        
        # check if record exists
        sqlStatement = "SELECT * FROM %s WHERE symbol = '%s' AND analysis_name = '%s'" % (
            tablename, symbol, analysis_name)
        cursor = self.conn.execute(sqlStatement)
        data = cursor.fetchall()
        
        # update or add record
        if len(data) > 0:
            sqlStatement = "UPDATE %s SET last_update_date = '%s' WHERE symbol = '%s' AND analysis_name = '%s'" % (
                tablename, currentdate, symbol, analysis_name)
            self.conn.execute(sqlStatement)
            self.conn.commit()
            print(' %s:[green] Updated %s %s[/green]' % (datetime.datetime.now(),symbol, analysis_name))
        else:
            sqlStatement = "INSERT INTO %s (symbol, analysis_name, last_update_date) VALUES ('%s', '%s', '%s')" % (
            tablename, symbol, analysis_name, currentdate)
            self.conn.execute(sqlStatement)
            self.conn.commit()
            print(' %s:[green] Added %s %s[/green]' % (datetime.datetime.now(), symbol, analysis_name))
    
    """
        Private function, saves optimized variables for momo vs. fwd returns correlation 
        inputs:
            symbol str
            momoPeriod [] 
            fwdReturnPeriod []
    """
    def _save_opt_momo_fwdReturns(self, symbol, momoPeriod, fwdReturnPeriod, correl):
        tablename = 'opt_momo_fwdReturn'
        # set correl to 9 sig figs
        correl = [round(x, 9) for x in correl]
        sqlStatement = "INSERT INTO %s (symbol, momoPeriod, fwdReturnPeriod, correl, date_added) VALUES ('%s', '%s', '%s', '%s', '%s')" % (
            tablename, symbol, momoPeriod, fwdReturnPeriod, correl, datetime.datetime.now())
        self.conn.execute(sqlStatement)
        self.conn.commit()
        
    
    ############################################################
    ##################### PUBLIC FUNCTIONS #####################
    ############################################################
    """ 
        Saves optimized analysis variables to db, handles all analysis types    
        Inputs: 
            [str] symbol
            [str] analysis_name 
            [df] variables 
    """
    def save_opt_variables(self, symbol, analysis_name, variables):
        if analysis_name == 'opt_momo_fwdReturn':
            self._save_opt_momo_fwdReturns(symbol, variables['momoPeriod'].tolist(), variables['fwdReturnPeriod'].tolist(), variables['correl'].tolist())
            self._update_analysis_metadata(symbol, analysis_name)

    """
        Retrieves analysis variables 
        Inputs: 
            symbol
            analysis_name
        Returns false if none found 
    """
    def get_analysis_variables(self, symbol, analysis_name):
        tablename = analysis_name
        sqlStatement = "SELECT * FROM %s WHERE symbol = '%s'" % (
            tablename, symbol)
        
        data2 = pd.read_sql_query(sqlStatement, self.conn)
        
        if not data2.empty:
            return data2
        else:
            return None


# Usage example:
#db = AnalysisOptimizationsDB(config.dbname_analysisOptimizations)
#db.connect()

# add mock data 
#df = pd.DataFrame({'momoPeriod': [12,13,42], 'fwdReturnPeriod': [10,12,32]})
#db.save_opt_variables('SPY', 'opt_momo_fwdReturn', df)

# retrieve mock data 
#savedOpt = db.get_analysis_variables('GBT', 'opt_momo_fwdReturn')
#print(savedOpt)
 
#db.disconnect()
