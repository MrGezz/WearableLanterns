scriptname _WL_VendorStock extends Quest

Armor property _WL_WearableLanternInvDisplay auto
Armor property _WL_WearableTorchbugApparel_EmptyInvDisplay auto

;===Hotfix 3.0b: Auxiliary properties with new names to fix vendor inventory bug
Armor property TravelLanternItem auto
Armor property TorchbugLanternItem auto

Book property _WL_Manual auto
MiscObject property _WL_LanternOil4 auto

ReferenceAlias property RiverwoodTraderChestAlias auto
ReferenceAlias property CaravanAChestAlias auto
ReferenceAlias property CaravanBChestAlias auto
ReferenceAlias property CaravanCChestAlias auto
ReferenceAlias property AvalAtheronChestAlias auto
ReferenceAlias property BethethorsChestAlias auto
ReferenceAlias property BirnaChestAlias auto
ReferenceAlias property BrandChestAlias auto
ReferenceAlias property PawnedPrawnChestAlias auto
ReferenceAlias property WhiterunFraliaChestAlias auto
ReferenceAlias property SolitudeBitsAndPiecesChestAlias auto
ReferenceAlias property ArnleifChestAlias auto
ReferenceAlias property GrayPineGoodsChestAlias auto
ReferenceAlias property NiranyeChestAlias auto

ObjectReference property RiverwoodTraderMerchantContainer auto
ObjectReference property CaravanAChestREF auto
ObjectReference property CaravanBChestREF auto
ObjectReference property CaravanCChestREF auto
ObjectReference property AvalAtheronChest auto
ObjectReference property BethethorsMerchantChestRef auto
ObjectReference property BirnaChest auto
ObjectReference property BrandChest auto
ObjectReference property PawnedPrawnChest auto
ObjectReference property WhiterunFraliaChest auto
ObjectReference property MerchantSolitudeBitsAndPiecesChestRef auto
ObjectReference property ArnleifChest auto
ObjectReference property GrayPineGoodsChest auto
ObjectReference property NiranyeChest auto

Event OnInit()
	
	;Stock lantern items
	FillAllAliases()
	
	;Hotfix 3.0b: the clear/remove/fill cycle must run after the aliases have settled.
	;Deferred to OnUpdateGameTime instead of blocking the script thread with a 3s wait.
	RegisterForSingleUpdateGameTime(0.01)
	
endEvent

Event OnUpdateGameTime()

	;Clear the alias
	ClearAllAliases()
	
	;Remove any items found in any of the chests listed
	RemoveAllModItems()
	
	;Re-fill the alias
	FillAllAliases()
	
	RegisterForSingleUpdateGameTime(24)
	
endEvent

Function ClearAllAliases()

	;Clear all merchant chest aliases
	RiverwoodTraderChestAlias.Clear()
	CaravanAChestAlias.Clear()
	CaravanBChestAlias.Clear()
	CaravanCChestAlias.Clear()
	AvalAtheronChestAlias.Clear()
	BethethorsChestAlias.Clear()
	BirnaChestAlias.Clear()
	BrandChestAlias.Clear()
	PawnedPrawnChestAlias.Clear()
	WhiterunFraliaChestAlias.Clear()
	SolitudeBitsAndPiecesChestAlias.Clear()
	ArnleifChestAlias.Clear()
	GrayPineGoodsChestAlias.Clear()
	NiranyeChestAlias.Clear()
	
endFunction

Function FillAllAliases()

	;Fill aliases to apply their inventories
	RiverwoodTraderChestAlias.ForceRefIfEmpty(RiverwoodTraderMerchantContainer)
	CaravanAChestAlias.ForceRefIfEmpty(CaravanAChestREF)
	CaravanBChestAlias.ForceRefIfEmpty(CaravanBChestREF)
	CaravanCChestAlias.ForceRefIfEmpty(CaravanCChestREF)
	AvalAtheronChestAlias.ForceRefIfEmpty(AvalAtheronChest)
	BethethorsChestAlias.ForceRefIfEmpty(BethethorsMerchantChestRef)
	BirnaChestAlias.ForceRefIfEmpty(BirnaChest)
	BrandChestAlias.ForceRefIfEmpty(BrandChest)
	PawnedPrawnChestAlias.ForceRefIfEmpty(PawnedPrawnChest)
	WhiterunFraliaChestAlias.ForceRefIfEmpty(WhiterunFraliaChest)
	SolitudeBitsAndPiecesChestAlias.ForceRefIfEmpty(MerchantSolitudeBitsAndPiecesChestRef)
	ArnleifChestAlias.ForceRefIfEmpty(ArnleifChest)
	GrayPineGoodsChestAlias.ForceRefIfEmpty(GrayPineGoodsChest)
	NiranyeChestAlias.ForceRefIfEmpty(NiranyeChest)

endFunction

function RemoveAllModItems()

	;RemoveItem on a form that is not present is a no-op, so no GetItemCount test is needed.

	RiverwoodTraderMerchantContainer.RemoveItem(TravelLanternItem, 99)
	RiverwoodTraderMerchantContainer.RemoveItem(_WL_Manual, 99)
	RiverwoodTraderMerchantContainer.RemoveItem(_WL_LanternOil4, 99)
	RiverwoodTraderMerchantContainer.RemoveItem(TorchbugLanternItem, 99)
	
	CaravanAChestREF.RemoveItem(TravelLanternItem, 99)
	CaravanAChestREF.RemoveItem(_WL_Manual, 99)
	CaravanAChestREF.RemoveItem(_WL_LanternOil4, 99)
	CaravanAChestREF.RemoveItem(TorchbugLanternItem, 99)
	
	CaravanBChestREF.RemoveItem(TravelLanternItem, 99)
	CaravanBChestREF.RemoveItem(_WL_Manual, 99)
	CaravanBChestREF.RemoveItem(_WL_LanternOil4, 99)
	CaravanBChestREF.RemoveItem(TorchbugLanternItem, 99)
	
	CaravanCChestREF.RemoveItem(TravelLanternItem, 99)
	CaravanCChestREF.RemoveItem(_WL_Manual, 99)
	CaravanCChestREF.RemoveItem(_WL_LanternOil4, 99)
	CaravanCChestREF.RemoveItem(TorchbugLanternItem, 99)
	
	AvalAtheronChest.RemoveItem(TravelLanternItem, 99)
	AvalAtheronChest.RemoveItem(_WL_Manual, 99)
	AvalAtheronChest.RemoveItem(_WL_LanternOil4, 99)
	AvalAtheronChest.RemoveItem(TorchbugLanternItem, 99)
	
	BethethorsMerchantChestRef.RemoveItem(TravelLanternItem, 99)
	BethethorsMerchantChestRef.RemoveItem(_WL_Manual, 99)
	BethethorsMerchantChestRef.RemoveItem(_WL_LanternOil4, 99)
	BethethorsMerchantChestRef.RemoveItem(TorchbugLanternItem, 99)
	
	BirnaChest.RemoveItem(TravelLanternItem, 99)
	BirnaChest.RemoveItem(_WL_Manual, 99)
	BirnaChest.RemoveItem(_WL_LanternOil4, 99)
	BirnaChest.RemoveItem(TorchbugLanternItem, 99)
	
	BrandChest.RemoveItem(TravelLanternItem, 99)
	BrandChest.RemoveItem(_WL_Manual, 99)
	BrandChest.RemoveItem(_WL_LanternOil4, 99)
	BrandChest.RemoveItem(TorchbugLanternItem, 99)
	
	PawnedPrawnChest.RemoveItem(TravelLanternItem, 99)
	PawnedPrawnChest.RemoveItem(_WL_Manual, 99)
	PawnedPrawnChest.RemoveItem(_WL_LanternOil4, 99)
	PawnedPrawnChest.RemoveItem(TorchbugLanternItem, 99)
	
	WhiterunFraliaChest.RemoveItem(TravelLanternItem, 99)
	WhiterunFraliaChest.RemoveItem(_WL_Manual, 99)
	WhiterunFraliaChest.RemoveItem(_WL_LanternOil4, 99)
	WhiterunFraliaChest.RemoveItem(TorchbugLanternItem, 99)
	
	MerchantSolitudeBitsAndPiecesChestRef.RemoveItem(TravelLanternItem, 99)
	MerchantSolitudeBitsAndPiecesChestRef.RemoveItem(_WL_Manual, 99)
	MerchantSolitudeBitsAndPiecesChestRef.RemoveItem(_WL_LanternOil4, 99)
	MerchantSolitudeBitsAndPiecesChestRef.RemoveItem(TorchbugLanternItem, 99)
	
	ArnleifChest.RemoveItem(TravelLanternItem, 99)
	ArnleifChest.RemoveItem(_WL_Manual, 99)
	ArnleifChest.RemoveItem(_WL_LanternOil4, 99)
	ArnleifChest.RemoveItem(TorchbugLanternItem, 99)
	
	GrayPineGoodsChest.RemoveItem(TravelLanternItem, 99)
	GrayPineGoodsChest.RemoveItem(_WL_Manual, 99)
	GrayPineGoodsChest.RemoveItem(_WL_LanternOil4, 99)
	GrayPineGoodsChest.RemoveItem(TorchbugLanternItem, 99)
	
	NiranyeChest.RemoveItem(TravelLanternItem, 99)
	NiranyeChest.RemoveItem(_WL_Manual, 99)
	NiranyeChest.RemoveItem(_WL_LanternOil4, 99)
	NiranyeChest.RemoveItem(TorchbugLanternItem, 99)
	
endFunction