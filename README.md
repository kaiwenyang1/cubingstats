# CubingStats

## Introduction

This project is aimed at expanding the metrics used in WCA rankings and implement some cool statistics and metrics some cubers care about.
Currently it includes their PR streak with and without blind and fmc commpetitions. The next feature will be to include a ranking for the sum of ranks for competitors, which is a measurement for how well-rounded a particular competitor is. 

Another idea will be to include ranking history, which is to be able to see how the WCA rankings page looked like at any point in time. 

This uses Flask mainly, details of setup will be included later. The data is retrieved mainly with SQL from their database which can be found here: https://www.worldcubeassociation.org/export/results

This export is updated once every week.
