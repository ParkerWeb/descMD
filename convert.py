from lxml import etree
import os
import json
import codecs
import copy
import re

space = re.compile('\n[ ]+')
d = "split-xmls/description"
fix = lambda x: space.sub('', x)

baseUrl = "http://linked-data.stanford.edu/parker/ms/"

base = {
	"@context": {
		"bf": "http://bibframe.org/vocab/",
		"note": "http://stanford.edu/notes/ns/",
		"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
		"rdfs": "http://www.w3.org/2000/01/rdf-schema#",
		"value": "rdf:value",
		"type": "@type",
		"id": "@id",
		"@vocab": "http://bibframe.org/vocab/"
	},
	"type": "Work",
	"title": [{
			"type": "Title",
			"value": ""
		}
	],
	"hasInstance": {
		"type": "Manuscript",
		"hasItem": {
			"type": "Item",
			"heldBy": {
				"type": "Organization",
				"label": "Corpus Christi College"
			},
			"subLocation": "Parker Library",
			"identifiedBy": [],
			"note": []
		},
		"contains": []
	}
}


files = os.listdir(d)
for f in files:
	if f.endswith("xml"):

		# Load XML files
		n = f.replace('.xml', '')
		fh = file(os.path.join(d, f))
		data = fh.read()
		fh.close()
		data = data.replace('\r\n', '\n')
		data = codecs.decode(data, "ISO-8859-2")
		dom = etree.XML(data)

		js = copy.deepcopy(base)
		top = dom.xpath("/TEI/text/body/msDesc")[0]

		# Extract content from the XML and add to the JSON-LD
		msid = top.xpath('./msIdentifier/@xml:id')[0].strip()
		js['hasInstance']['hasItem']['identifiedBy'].append(
			{
				"type": "LocalIdentifier",
				"scheme": "CCC",
				"value": msid
			})

		js['id'] = baseUrl + msid + "_work"
		js['hasInstance']['id'] = baseUrl + msid + "_instance"
		js['hasInstance']['hasItem']['id'] = baseUrl + msid

		try:
			js['hasInstance']['hasItem']['identifiedBy'].append(
				{
					"type": "LocalIdentifier",
					"scheme": "Stanley",
					"value": top.xpath('./msIdentifier/altIdentifier[@type="Stanley"]/idno/text()')[0].strip()
				})			
		except:
			pass
		try:
			js['hasInstance']['hasItem']['identifiedBy'].append(
				{
					"type": "LocalIdentifier",
					"scheme": "TJames",
					"value": top.xpath('./msIdentifier/altIdentifier[@type="TJames"]/idno/text()')[0].strip()
				})			
		except:
			pass

		js['title'][0]['value'] = fix(top.xpath('./head/text()')[0].strip())
		try:
			js['title'].append(
				{
					"type": "VariantTitle",
					"variantType": "James",
					"value": fix(top.xpath('./head[@type="James"]/text()')[0].strip())

				}
			)
		except:
			pass

		try:
			js['hasInstance']['hasCarrier'] = {"value": top.xpath('./p[function="Codicology"]/material/text()')[0].strip()}
		except:
			pass

		try:
			js['hasInstance']['dimensions'] = "%s x %s" % (top.xpath('./p[function="Codicology"]/measureGrp/height/text()')[0].strip(), 
				top.xpath('./p[function="Codicology"]/measureGrp/width/text()')[0].strip())
		except:
			pass


		try:
			js['hasInstance']['extent'] = top.xpath('./p[function="Codicology"]/measureGrp/extent/text()')[0].strip()
		except:
			pass

		try:
			js['hasInstance']['language'] = top.xpath('./msContents/textLang/text()')[0].strip()
		except:
			pass

		try:
			js['hasInstance']['production'] = {'date': fix(top.xpath('./p[function="Codicology"]/measureGrp/origDate/text()')[0])}
		except:
			pass

		try:
			js['hasInstance']['hasItem']['note'].append(
					{
						"type": "note:HandNote",
						"value": fix(top.xpath('./p[function="Codicology"]/measureGrp/handNote/text()')[0])
					}
				)
		except:
			pass

		try:
			js['hasInstance']['hasItem']['note'].append(
					{
						"type": "note:IllustrationNote",
						"value": fix(top.xpath('./p[function="Codicology"]/measureGrp/decoNote/text()')[0])
					}
				)
		except:
			pass

		try:
			js['hasInstance']['hasItem']['note'].append(
					{
						"type": "note:FoliationNote",
						"value": fix(top.xpath('./p[function="CCC"]/foliation/text()')[0])
					}
				)
		except:
			pass

		try:
			js['hasInstance']['hasItem']['note'].append(
					{
						"type": "note:ProvenanceNote",
						"value": fix(''.join(top.xpath('./p[function="Provenance"]//text()')))
					}
				)
		except:
			pass

		for msi in top.xpath('./msContents/msItem'):
			try:
				js['hasInstance']['contains'].append({
					"type": "Instance",
					"title": {
						"type": "Title",
						"value": fix(''.join(msi.xpath('./head[@type="CCC"]//text()')).strip())
					}	
				})
			except:
				continue
			try:
				js['hasInstance']['contains'][-1]['extent'] = "%s-%s" % (msi.xpath('./@locusStart')[0].strip(), msi.xpath('./@locusEnd')[0].strip())
			except:
				pass


		# Finally write out the JSON-LD
		out = json.dumps(js, sort_keys=True, indent=2, separators=(',', ': '))
		fh = codecs.open("jsonld/%s.jsonld" % n, "w", "utf-8")
		fh.write(out)
		fh.close()
