"""
# (C) Copyright 2016 SLU Global Bioinformatics Centre, SLU
# (http://sgbc.slu.se) and the B3Africa Project (http://www.b3africa.org/).
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the GNU Lesser General Public License
# (LGPL) version 3 which accompanies this distribution, and is available at
# http://www.gnu.org/licenses/lgpl.html
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# Contributors:
# Rafael Hernandez de Diego
# Tomas Klingstrom
# Erik Bongcam-Rudloff
# and others.
#
# Updated for Galaxy 25.0 compatibility
"""

from os import path as osPath
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.objects import GalaxyInstance as GalaxyInstanceObjects
import logging

def generateWorkflowReport(request, settings):
    """
    Generate a workflow report using Galaxy 25.0 compatible API calls
    """
    try:
        # Get the invocation and workflow data
        invocation = request.json.get("invocation")
        workflow = request.json.get("workflow")
        
        # Open a new connection with bioblend
        galaxy_key = request.values.get("key")
        gi = GalaxyInstance(settings.GALAXY_SERVER, galaxy_key)
        
        # Use objects API for better compatibility
        gi_objects = GalaxyInstanceObjects(settings.GALAXY_SERVER, galaxy_key)
        
        workflow_steps = {}
        for step in workflow.get("steps"):
            workflow_steps[step.get("uuid")] = step
            
        for step in invocation.get("steps"):
            workflow_step = workflow_steps[step.get("workflow_step_uuid"))
            workflow_step["state"] = step.get("state")
            workflow_step["job_id"] = step.get("job_id")
            
            try:
                # Get job information with error handling
                job_info = gi.jobs.show_job(step.get("job_id"))
                workflow_step["job"] = job_info
            except Exception as e:
                logging.warning(f"Could not get job info for job {step.get('job_id')}: {str(e)}")
                workflow_step["job"] = {"error": str(e)}
        
        # GENERATE THE HTML
        html_code = ""
        to_close_tags = []
        
        html_code += addTag("h2", "Workflow details", "font-size: 30px; color:red")
        html_code += getEntryLine("Workflow name", workflow.get("name"), "font-size: 30px; color:red")
        
        html_code += openNewSection("div", "font-size: 20px;", to_close_tags)
        html_code += getEntryLine("Workflow name", workflow.get("name"))
        html_code += getEntryLine("Owner", workflow.get("owner"))
        html_code += getEntryLine("Run date", invocation.get("update_time"))
        html_code += closeSection(to_close_tags)
        
        # Add workflow steps information
        html_code += openNewSection("div", "font-size: 16px;", to_close_tags)
        html_code += addTag("h3", "Workflow Steps")
        
        for step_uuid, step in workflow_steps.items():
            html_code += openNewSection("div", "margin-bottom: 15px; padding: 10px; border: 1px solid #ccc;", to_close_tags)
            html_code += addTag("h4", step.get("name", "Unnamed Step"))
            html_code += getEntryLine("Step ID", step_uuid)
            html_code += getEntryLine("State", step.get("state", "unknown"))
            
            if "job" in step and isinstance(step["job"], dict):
                job = step["job"]
                html_code += getEntryLine("Job ID", job.get("id", "N/A"))
                html_code += getEntryLine("Job State", job.get("state", "N/A"))
                
                if "error" in job:
                    html_code += addTag("p", f"Error: {job['error']}", "color: red;")
            
            html_code += closeSection(to_close_tags)
        
        html_code += closeSection(to_close_tags)
        
        # Save the HTML report
        report_filename = f"workflow_report_{invocation.get('id', 'unknown')}.html"
        report_path = osPath.join(settings.TMP_DIRECTORY, report_filename)
        
        with open(report_path, 'w') as f:
            f.write(html_code)
        
        return report_path
        
    except Exception as e:
        logging.error(f"Error generating workflow report: {str(e)}")
        raise

def addTag(tag, content, style=""):
    """Add HTML tag with content and optional style"""
    style_attr = f' style="{style}"' if style else ""
    return f"<{tag}{style_attr}>{content}</{tag}>"

def getEntryLine(key, value, style=""):
    """Generate a styled entry line"""
    if value is None:
        value = "N/A"
    return addTag("p", f"<strong>{key}:</strong> {value}", style)

def openNewSection(tag, style, to_close_tags):
    """Open a new section and keep track of closing tags"""
    to_close_tags.append(tag)
    return f"<{tag} style='{style}'>"

def closeSection(to_close_tags):
    """Close the last opened section"""
    if to_close_tags:
        tag = to_close_tags.pop()
        return f"</{tag}>"
    return ""
