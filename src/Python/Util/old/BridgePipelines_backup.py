import sys,os
from collections import defaultdict as dd

# PHENO

class BridgePipelines:
    def __init__(self,io): 
        self.args, self.io, self.module, self.cmd, self.settings = io.args, io, io.module, io.cmd, io.settings 
        self.eType, self.wType, self.FIN = 'BridgePipelineError:', 'BridgePipelineWarning:', dd(bool)
        self.input_key = dd(lambda: dd(bool)) 
        if self.module != 'analyze': self.create() 


    def create(self): 
        self.commands, self.pop = [self.cmd], self.settings.pop.name 
        if self.module in ['pipeline','easyrun']: 
            self.pop1, self.pop2 = self.args.pop 
            if self.module == 'pipeline' and not self.args.port: command_list = ['prs-single','prs-prior','prs-combined'] 
            else:                                                command_list = ['prs-single','prs-prior','prs-port','prs-combined'] 
            for i,x in enumerate(command_list): 
                dir1 = x+'_'+self.pop1 
                if x in ['prs-single','prs-prior']: self.add_dirs(self.io.paths['home']+'/'+dir1, ['clump','beta','predict','quantify'])
                elif x == 'prs-port':               self.add_dirs(self.io.paths['home']+'/'+dir1, ['predict','quantify'])
                else:                               self.add_dirs(self.io.paths['home']+'/'+dir1, []) 
                progress_file = self.io.paths['home']+'/'+dir1+'/bridge.'+x+'.result'
                if not os.path.isfile(progress_file): 
                    w = open(progress_file,'w')  
                    w.write('POP='+self.pop1+'\nMODULE_NAME='+x+'\n') 
                    w.close()
            self.add_dirs(self.io.paths['home']+'/model_'+self.pop2, ['clump','beta','predict','prior']) 
            progress_file = self.io.paths['home']+'/model_'+self.pop2+'/bridge.build-model.result'
            if not os.path.isfile(progress_file): 
                w = open(progress_file,'w')  
                w.write('POP='+self.pop2+'\nMODULE_NAME=build-model\n') 
                w.close()
            return 
        else:
            if self.module.split('-')[0] == 'prs': 
                self.io.paths['run'] = self.io.paths['home']+'/'+self.module+'_'+self.pop 
                if self.cmd == 'run': 
                    if self.module.split('-')[-1] == 'port':      self.commands = ['predict','quantify'] 
                    else:                                         self.commands = ['clump','beta','predict','quantify'] 
                else:                                             self.commands = [self.cmd] 
            elif self.module == 'build-model': 
                self.io.paths['run'] = self.io.paths['home']+'/model_'+self.pop 
                if self.cmd == 'run': self.commands = ['clump','beta','predict','prior'] 
                else:                 self.commands = [self.cmd] 
            else: self.io.progress.fail('Unsupported Module') 
            self.progress_file = self.io.paths['run']+'/bridge.'+self.module+'.result'
            self.add_dirs(self.io.paths['run'], self.commands) 
            if not os.path.isfile(self.progress_file): 
                w = open(self.progress_file,'w')  
                w.write('POP='+self.pop+'\n') 
                w.write('MODULE_NAME='+self.module+'\n')
                w.close()
            return  








    def add_dirs(self,parent,children,grandchildren=[]):
        if not os.path.exists(parent): os.makedirs(parent)
        for c in children:
            if not os.path.exists(parent+'/'+c): os.makedirs(parent+'/'+c)
            self.io.paths[c] = parent+'/'+c 
            if c == 'prior': 
                if not os.path.exists(parent+'/'+c+'/lambda'): os.makedirs(parent+'/'+c+'/lambda') 
            for g in grandchildren:
                if not os.path.exists(parent+'/'+c+'/'+g): os.makedirs(parent+'/'+c+'/'+g)
                self.io.paths[g] = parent+'/'+c+'/'+g 
    

    

    def verify_pipeline(self):

        if self.module in ['easyrun','pipeline','analyze']: return self  
        self.command_strings = []
        for i,c in enumerate(self.commands):
            JN = ' ('+self.module+' '+c+')'
            if c == 'clump': self.command_strings.append('Clumping Pop Data'+JN) 
            elif c == 'beta': self.command_strings.append('Calculating SNP Weights'+JN) 
            elif c == 'predict': self.command_strings.append('Generating Polygenic Predictions'+JN) 
            elif c == 'quantify': self.command_strings.append('Quantifying PRS Result'+JN) 
            elif c == 'prior': self.command_strings.append('Saving SNP Priors'+JN) 
            else:            self.command_strings.append(c) 
        for X1,X2 in self.progress_pair(): 
            xsp = X1.split('_') 
            if len(xsp) == 3 and xsp[0] == self.pop: 
                x_pop, x_job, x_val = xsp 
                if x_val == 'FIN':      self.FIN[x_job] = True  
                elif x_val == 'PREFIX': self.input_key['prefix'][x_job.lower()] = X2 
                elif x_val == 'FILE':   self.input_key['file'][x_job.lower()]   = X2 
                else:                   self.io.progress.fail('Bad Key',ETYPE=self.eType)                   
            elif len(xsp) == 2: 
                if xsp[-1] == 'FILE': self.input_key['file'][xsp[0].lower()] = X2 
                elif xsp[0] == 'FIELD': 
                    f_type, f_name = xsp[1].split('-') 
                    if f_type == 'PHENO': self.input_key['pf-'+f_name.lower()] = X2  
                    else:                 self.io.progress.fail(['Bad Ftype',f_type],ETYPE=self.eType)  
        return self

    
    def progress_pair(self):
        p_handle = open(self.progress_file) 
        progress_pair = [x.strip().split('=') for x in p_handle.readlines()]  
        p_handle.close() 
        return progress_pair 



    def log_result(self, d): 
        fD, fI, f_pass, f_obs = self.io.settings, self.io.settings.pop, dd(bool), [] 
        np, fp, D = self.pop+'_'+d, self.io.paths['run']+'/'+d, d.upper() 
        
        #for line in open(fI.config,'rt'): 
        
        f_pairs = [line.strip().split('=') for line in open(fI.config,'rt')]
        f_pairs.extend([[X1,X2] for X1,X2 in self.progress_pair() if X1.split('_')[0] != self.pop or X1.split('_')[1] != D]) 
        if fI.genopheno.VALID: 
            f_pairs.append(['PHENOTYPE_FILES',",".join(fI.genopheno.files)])
            for x,y in fI.genopheno.fields.items():  f_pairs.append(['PHENOTYPE_FIELD-'+x,y]) 
            f_pairs.append(['PHENOTYPE_TYPE',fI.genopheno.type]) 
        #if fI.sumstats.VALID:    f_pairs.append(['SNP_FILE',fI.sumstats.snp_file])
        #if fI.bdata.VALID:       f_pairs.append(['ID_FILE',fI.bdata.id_file]) 
        if 'model' in fD.files and fD.files['model'] is not None: f_pairs.append(["MODEL_FILE",fD.files['model']]) 
        self.validate_path(np,fp, D) 
        self.io.settings.prefixes[d] = fp+'/'+np  
        f_pairs.extend([[self.pop+'_'+D+'_PREFIX',fp+'/'+np],[self.pop+'_'+D+'_FIN','TRUE']])             
        w = open(self.progress_file,'w') 
        for a,b in f_pairs: 
            if a not in f_obs: w.write(a+'='+b+'\n') 
            f_obs.append(a) 
        w.close() 
        return 



    def validate_path(self, np, fp, D): 
        if not os.path.isdir(fp): self.io.progress.fail('EXITED UNSUCCESSFULLY',ETYPE=self.eType) 
        d_files =   [fn for fn in os.listdir(fp) if fn.split('.')[-1] not in ['log','tmp']] 
        err_files, res_files = [fn for fn in d_files if fn.split('.')[-1] == 'stderr'], [fn for fn in d_files if np in fn]
        self.check_error_output(fp, err_files, D) 
        if len(res_files) < 1: self.io.progress.fail('EXITED UNSUCCESSFULLY; NO OUTPUT CREATED',ETYPE=self.eType) 
        return 



    def check_error_output(self, fp, err_files, D): 
        if len(err_files) != 1: self.io.progress.fail('EXITED UNSUCCESSFULLY', ETYPE=self.eType) 
        
        f_errors, f_handle = [], open(fp+'/'+err_files[0]) 
        
        #if D not in ['CLUMP','BETA','PREDICT']: 
        #    err_files = ['/home/tade/Current/bridgePRS/repo/tests/pedro/quantify.stderr']
        #    f_handle = open(err_files[0]) 
        f_lines = [lp.strip() for lp in f_handle] 
        f_handle.close()
        
        for lp in f_lines: 
            ls = [x.lower() for x in lp.split()] 
            if len(ls) < 1: continue 
            elif ls[0][0:4] in ['warn','extr','load','usag','lade']: continue  
            else: 
                if D == 'CLUMP': 
                    if " ".join(ls[-3::]) == 'see log file.': continue  
                    if len(ls) > 3 and ls[3] == 'ignored,':   continue 
                if len(ls[0].split('/'))>1: ls[0] = ls[0].split('/')[-1] 
                f_errors.append(' '.join(ls)) 
       
        if len(f_errors) == 0: return
        else:                  self.io.progress.warn(['UNKNOWN R-OUTPUT IN STDERR (Program may have failed):']+f_errors, WTYPE=self.wType) 
        return
        #self.io.progress.fail(['EXITED UNSUCCESSFULLY']+f_errors, ETYPE=self.eType) 
        







