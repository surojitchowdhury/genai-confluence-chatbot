from atlassian import Confluence
import os
import requests
import html2text

from dotenv import load_dotenv

load_dotenv()

def __get_page_id(confluence, id_):
        if isinstance(id_, tuple):
            id_ = confluence.get_page_id(id_[0], id_[1])
        return id_
    
def get_page_tree_ids(confluence, id_):
        page = get_page(confluence, id_, full_info=False)
        ret = [page['id']]
        children_ids = [r['id'] for r in page['children']['page']['results']]
        for id_ in children_ids:
            ret += get_page_tree_ids(confluence, id_)
        
        return ret
    

def get_page(confluence, id_, full_info=True):
        id_ = __get_page_id(confluence, id_)

        expand = 'children.page.id'
        if full_info:
            expand = 'version,body.storage,children.page.id'

        raw = confluence.get_page_by_id(id_, expand=expand)
        return raw
        
def get_and_write_page(confluence, page_id):
    page_info = get_page(confluence, page_id, full_info=True)
    # Create the filename
    filename = os.path.join(pages_folder, f"{page_info['title'].replace(' ','_')}.txt")
    # Get the content of the page
    page_content = confluence.get_page_by_id(page_id, expand='body.storage')['body']['storage']['value']
    page_downloaded.add(page_id)
    
    page_text = html2text.html2text(page_content)
    page_text += "\n\n\n source_page_webui:"+page_info['_links']['base']+page_info['_links']['webui']
    
    # Write the content to a file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html2text.html2text(page_text))
    except Exception as e_msg:
        print(f"Unable to write file for error: {e_msg}")

def get_all_recursive_pages(confluence, all_pages):
    # Loop through each page and store it in a file
    for page in all_pages:
        page_id = page['id']
        
        get_and_write_page(confluence, page_id)

        # Get all child pages if any
        id_dict_list = []
        ret = get_page_tree_ids(confluence, page_id)
        for id in ret:
            if id not in page_downloaded:
                id_dict_list.append({"id": id})
        if len(id_dict_list)!=0:
            get_all_recursive_pages(confluence, id_dict_list)
  
def main():          
	# Set up the Confluence API instance
	confluence_url = os.environ['CONFLUENCE_URL']
	username = os.environ['CONFLUENCE_USERNAME']
	password = os.environ['CONFLUENCE_API_KEY']
	confluence = Confluence(
	    url=confluence_url,
	    username=username,
	    password=password
	)
	
	# Set up the folder to store Confluence pages
	pages_folder = 'confluence_pages'
	if not os.path.exists(pages_folder):
	    os.makedirs(pages_folder)
	
	page_downloaded = set()
	
	space='Confluence'
	all_pages = confluence.get_all_pages_from_space(space)
	
	get_all_recursive_pages(confluence, all_pages)
	print("Page downloads completed!")

if __name__ == "__main__":
    main()