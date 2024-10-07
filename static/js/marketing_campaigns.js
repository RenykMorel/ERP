document.addEventListener('DOMContentLoaded', function() {
    const campaignList = document.getElementById('campaign-list');
    const createCampaignForm = document.getElementById('create-campaign-form');

    function loadCampaigns() {
        fetch('/marketing/api/campaigns')
            .then(response => response.json())
            .then(campaigns => {
                campaignList.innerHTML = campaigns.map(campaign => `
                    <div>
                        ${campaign.name} - ${campaign.subject}
                        ${campaign.sent_at ? `Enviado: ${campaign.sent_at}` : `
                            <button onclick="sendCampaign(${campaign.id})">Enviar</button>
                        `}
                    </div>
                `).join('');
            });
    }

    createCampaignForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('campaign-name').value;
        const subject = document.getElementById('campaign-subject').value;
        const content = document.getElementById('campaign-content').value;

        fetch('/marketing/api/campaigns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, subject, content }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            loadCampaigns();
            createCampaignForm.reset();
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });

    window.sendCampaign = function(campaignId) {
        fetch(`/marketing/api/send_campaign/${campaignId}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            console.log('Campaign sent:', data);
            loadCampaigns();
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    };

    loadCampaigns();
});