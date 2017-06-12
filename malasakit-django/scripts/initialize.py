import environment

from pcari.models import Comment, User

u = User.objects.all().filter(username="admin")[0]

for c in Comment.objects.all():
    if c.user == u:
        c.delete()


filipino = [
    "Pagsasagawa ng drill upang magkaroon ng kaalaman ang mga tao kung ano ang gagawin nila sa oras ng sakuna",
    "Group text message, Social Media at Local News Announcement (specific barangay per city)",
    "Siguraduhin na malinis ang mga kanal, magkaroon ng mga water pumps",
    "Nakabubuti na mamigay ang barangay ng mga pamphlets na naglalaman ng mga numero ng mga ahensyang makatutulong sa mga pwedeng dumating na sakuna",
    "Magkaroon ng mas epektibong disaster drill at seminars sa bawat parte ng barangay para sa mas handang komunidad",
    "Nagbibigay ng relief goods kung ito ay kailanganin at nagsasabi sila kapag kailangan na naming lumikas sa aming tahanan",
    "Higit na magiging handa kami sa isang malakas na bagyo o pagbaha kung magsasagawa ang barangay ng 'disaster drill' at kung magkakaroon ng 'unified text messaging system' ang barangay kung saan mabibigyan kami ng barangay ng update tungkol sa kalagayan ng barangay sa gitna ng bagyo o baha tulad ng kung saang lugar ang baha at kung saan safe pumunta",
    "Public address system, continuing education and training on disaster management",
    "Nagpapatunog ng serena, nag te-text sa mga area leader, nagiikot ang mga tanod ",
    "Pagpapatuloy ng pagaayos ng ilog upang lalong mapalalim; pagtulong sa pagpapaayos ng mga nasirang bahay; pagbibigay ng relief sa maayos na paraan"
]




english = [
    "Hold drill exercises so that people would know what to do in times of disasters.",
    "Group text message, Social Media at Local News Announcement (specific barangay per city)",
    "Ensure that the water ways are clean and there are water pumps available.",
    "It would help for the barangay to distribute pamphlets containing emergency hotline numbers.",
    "More effective disaster drills and seminars for every part of the barangay so that the community will be more prepared.",
    "The barangay should give relief goods when needed and they should announce if it is time for us to evacuate our homes.",
    "We will be better prepared if the barangay will hold a disaster drill and if there will be a unified text messaging system where we will be better informed and updated about the typhoon or flood situation; like which areas will be flooded and which areas are safe for evacuation.",
    "Public address system, continuing education and training on disaster management",
    "The barangay sounds the siren and texts the area leaders, and the barangay wardens road around.",
    "Continuous repair of the river to make it deeper; help mend broken houses; provide relief goods in an orderly fashion."
]

for i in range(len(filipino)):
    c = Comment(user=u, comment=english[i], filipino_comment=filipino[i], original_language="English")
    c.save()
