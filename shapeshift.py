from functools import wraps
import requests
import time
from requests.utils import quote

class ShiftProvider(object):
	def __init__(self,tld,apiroot):
		self.domain=tld
		self.apiroot=apiroot
		
		try:
			#logininfo load here
			#self.logininfo=open('
			raise "Not implemented"
		except:
			self.logininfo=None
	def allpairs(self):
		return []
		
def cached(invalidate_delay):
	def fdelay(f): 
		@wraps(f)
		def wrapper(s,*args, **kwds):
			argrep=str(args)+":"+str(kwds)
			try:
				lasttime=f.lastcalltime[argrep]
			except AttributeError:
				lasttime=0
				f.lastcalltime={}
				f.cached_result={}
			except KeyError:
				lasttime=0
				
			thistime=time.time()
			if((thistime-lasttime) < invalidate_delay):
				return f.cached_result[argrep]
			else:
				result=f(s,*args,**kwds)
				f.cached_result[argrep]=result
				f.lastcalltime[argrep]=thistime
				return result
		return wrapper
	return fdelay
		
	
class ShapeShift_io(ShiftProvider):
	def __init__(self):
		super(ShapeShift_io,self).__init__("shapeshift.io","https://shapeshift.io")
	
	def _makerequest(self,rfunc,path,*args,**kwargs):
		fullpath=self.apiroot+path
		result=rfunc(fullpath,*args,**kwargs).json()
		if('error' in result):
			raise Exception('Error calling %s:"%s"' % (fullpath,result['error']))
		return result
	
	@cached(60*60*2)
	def _allcoins(self):
		result=self._makerequest(requests.get,"/getcoins")
		return [k for k,v in result.items() if v["status"]=="available"]
		
	def allpairs(self):
		coins=self._allcoins()
		allpairs={}
		for c1 in coins:
			allpairs[c1]=list(coins)
		return allpairs
	def _pairserialize(self,pair):
		return "%s_%s" % (pair[0].lower(),pair[1].lower())
	
	@cached(60*2)
	def _marketinfo(self,pairarg=None):
		if(pairarg is None):
			result=self._makerequest(requests.get,"/marketinfo")
			return {minfo["pair"]:minfo for minfo in result}
		else:
			ps=self._pairserialize(pairarg)
			result=self._makerequest(requests.get,"/marketinfo/"+ps)
			return result
			
	@cached(60*2)
	def _validate_address(self,coin,addr):
		addr=quote(addr)
		result=self._makerequest(requests.get,"/validateAddress/"+addr+"/"+coin)
		
	def _validate_limit(self,out_amount,minfo):
		in_amount=out_amount/minfo["rate"]
		if(in_amount < minfo["min"]):
			raise Exception("Estimated coin deposit amount is below the minimum allowed")
		elif(in_amount > minfo["limit"]):
			raise Exception("Estimated coin deposit amount is above the minimum allowed")
		return in_amount
		
	#returns the transaction data necessary to verify.  This data is a dict that as 'address' as a key, and optionally "in_amount"
	def create_transaction(coin1,coin2,out_address,out_amount=None,return_address=None,validate_addresses=True,validate_limits=True):
		if(validate_addresses):
			self._validate_address(coin2,out_address)
			if(return_address is not None):
				self._validate_address(coin1,return_address)
		pair=self._pairserialize(coin1,coin2)
		pdata={'withdrawal':out_address,'pair':pair}
		if(return_address is not None):
			pdata['returnAddress']=return_address
			
		if(out_amount is None):
			result=self._makerequest(requests.post,"/shift",json=pdata)
		else:
			if(validate_limits):
				minfo=self._marketinfo(coin1,coin2)
				est_in_amount=self._validate_limit(out_amount,minfo)
			pdata['amount']=out_amount
			result=self._makerequest(requests.post,"/sendamount",json=pdata)
			result['in_amount']=result['depositAmount']
		result["address"]=result["deposit"]
		return result
	def check_transaction(txinfo):
		pass #uses a shiftinfo function as returned from create_transaction to 
sio=ShapeShift_io()
#print(sio.allpairs())
k=len(str(sio._marketinfo(("BTC","LTC"))))
print(k)
